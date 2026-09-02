import re
import json
import logging
from typing import Dict, Any, List, Optional
from core.gemini import ask_gemini
from modules.cinema_matchmaker.storage import (
    get_user_cinema_memory,
    add_or_update_movie_feedback,
    set_last_recommended_movies,
    get_last_recommended_movies,
    update_user_taste_profile
)

logger = logging.getLogger("CinemaMatchmaker")


async def recommend_movies(user_id: int, query: str, force_new_recommendation: bool = False) -> Dict[str, Any]:
    """
    Cognitive AI Film Sommelier with Thought Process and Taste Memory.
    Analyzes user feedback, tracks watched movies (liked/disliked), learns style preferences,
    and returns 5 finely-tuned movie recommendations excluding already seen titles.
    """
    user_mem = get_user_cinema_memory(user_id)
    watched: List[Dict[str, Any]] = user_mem.get("watched_movies", [])
    taste_summary: str = user_mem.get("taste_summary", "")
    favorite_genres: List[str] = user_mem.get("favorite_genres", [])
    favorite_directors: List[str] = user_mem.get("favorite_directors", [])
    disliked_tropes: List[str] = user_mem.get("disliked_tropes", [])
    last_recommended: List[Dict[str, Any]] = get_last_recommended_movies(user_id)

    # Format watched history for prompt
    liked_titles = [f"{w['title']}" + (f" ({w['director']})" if w.get('director') else "") + (f" - «{w['note']}»" if w.get('note') else "") for w in watched if w.get("status") == "liked"]
    disliked_titles = [f"{w['title']}" + (f" ({w['director']})" if w.get('director') else "") + (f" - «{w['note']}»" if w.get('note') else "") for w in watched if w.get("status") == "disliked"]
    neutral_titles = [f"{w['title']}" for w in watched if w.get("status") == "watched"]

    last_rec_summary = []
    for idx, m in enumerate(last_recommended, 1):
        ru = m.get("title_ru", "")
        orig = m.get("title_orig", "")
        dir_name = m.get("director", "")
        last_rec_summary.append(f"#{idx}: {ru} ({orig}, реж. {dir_name})")

    liked_str = "; ".join(liked_titles) if liked_titles else "Пока нет записей"
    disliked_str = "; ".join(disliked_titles) if disliked_titles else "Пока нет записей"
    neutral_str = "; ".join(neutral_titles) if neutral_titles else "Нет"
    fav_dirs_str = ", ".join(favorite_directors) if favorite_directors else "Пока не выделены"
    fav_genres_str = ", ".join(favorite_genres) if favorite_genres else "Пока не выделены"
    disliked_tropes_str = ", ".join(disliked_tropes) if disliked_tropes else "Нет"
    last_rec_str = "\n".join(last_rec_summary) if last_rec_summary else "Ранее рекомендаций в сессии не было"

    context_prompt = f"""Ты — профессиональный кинокритик, эксперт киноискусства и персональный AI-Киносомелье с непрерывной памятью и когнитивным блоком мышления.

=== ИЗВЕСТНЫЙ ПРОФИЛЬ ВКУСА ПОЛЬЗОВАТЕЛЯ ===
• Сформированный вкус: {taste_summary or 'Формируется (пока мало оценок)'}
• Любимые режиссеры: {fav_dirs_str}
• Любимые жанры/стили: {fav_genres_str}
• Не нравится / избегать: {disliked_tropes_str}
• 👍 ПОНРАВИЛИСЬ (просмотрено): {liked_str}
• 👎 НЕ ПОНРАВИЛИСЬ (просмотрено): {disliked_str}
• 👀 Просто просмотрено: {neutral_str}
===============================================

=== ПОСЛЕДНИЕ 5 РЕКОМЕНДАЦИЙ БОТА В ЭТОМ ЧАТЕ ===
{last_rec_str}
=================================================

ВХОДЯЩЕЕ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ: «{query}»

ТВОЙ МЫСЛИТЕЛЬНЫЙ ПРОЦЕСС И ЗАДАЧИ:
1. [АНАЛИЗ ОБРАТНОЙ СВЯЗИ / ПАМЯТИ]:
   - Проанализируй сообщение: упоминает ли пользователь какой-то фильм (по названию или по номеру #1..#5 из прошлых рекомендаций), который он смотрел, и дает ли оценку (понравился, шедевр, не зашел, скучный, норм)?
   - Если ДА: выдели точное название фильма, статус ('liked' / 'disliked' / 'watched'), режиссера, жанр, причину/заметку.
   - Сформулируй блок 'thought_process' (краткий живой анализ: что бот понял, как это повлияло на понимание вкуса и что теперь будет учитываться в подборе).
   - Сформулируй 'new_taste_summary', дополни 'new_favorite_directors', 'new_favorite_genres', 'new_disliked_tropes' на основе всех данных.

2. [ПОДБОР 5 ТОП-ФИЛЬМОВ / СЕРИАЛОВ]:
   - Сгенерируй РОВНО 5 великолепных, неизбитых фильмов или сериалов под актуальный запрос с учетом ВСЕГО накопленного вкуса пользователя!
   - СТРОЖАЙШЕЕ ПРАВИЛО: НИ В КОЕМ СЛУЧАЕ не предлагай те фильмы, которые пользователь УЖЕ смотрел (списки ПОНРАВИЛИСЬ / НЕ ПОНРАВИЛИСЬ / ПРОСМОТРЕНО)!
   - В поле 'why_match' каждого фильма четко и аргументированно объясни связь со вкусом (например: «Поскольку вам понравился 'Залечь на дно в Брюгге', здесь такой же едкий черный юмор и меланхоличная атмосфера...»).
   - Укажи реальные рейтинги Кинопоиска (КП) и IMDb.
   - Укажи, где легально посмотреть в РФ (Кинопоиск, Иви, Okko, Start, Premier, KION, Wink).
   - Составь 'viewing_setup' (подходящий напиток, закуска, атмосфера вечера).

Верни ответ СТРОГО в формате JSON:
{{
  "thought_process": "🧠 Зафиксировал: фильм «Залечь на дно в Брюгге» вам очень понравился (👍). Обновил ваш профиль: повысил приоритет для диалоговых черных комедий, ирландского колорита и сценариев Мартина Макдоны. Исключаю его из будущих подборок.",
  "detected_feedback": [
    {{
      "title": "Залечь на дно в Брюгге",
      "status": "liked",
      "director": "Мартин Макдона",
      "genres": "Криминал, комедия, драма",
      "year": "2008",
      "note": "Понравились черный юмор и диалоги"
    }}
  ],
  "new_taste_summary": "Ценитель остроумного британского и ирландского криминала, авторских черных комедий и динамичных диалоговых драм.",
  "new_favorite_directors": ["Мартин Макдона", "Гай Ричи"],
  "new_favorite_genres": ["Черная комедия", "Криминал", "Неонуар"],
  "new_disliked_tropes": ["Слащавые мелодрамы"],
  "mood_summary": "Искрометный циничный юмор и криминальные авантюры",
  "movies": [
    {{
      "title_ru": "Голгофа",
      "title_orig": "Calvary (2014)",
      "director": "Джон Майкл Макдона",
      "genres": "Драма, комедия, детектив",
      "ratings": "КП: 7.7 | IMDb: 7.4",
      "why_match": "Режиссер — родной брат Мартина Макдоны, в главной роли Брендан Глисон. Тот же фирменный ирландский сарказм и глубокий философский подтекст.",
      "plot_hook": "Сельский священник во время исповеди узнает, что через неделю его убьют, и решает провести оставшиеся дни, помогая прихожанам.",
      "where_to_watch": "Кинопоиск, Okko, Иви"
    }},
    {{
      "title_ru": "Семь психопатов",
      "title_orig": "Seven Psychopaths (2012)",
      "director": "Мартин Макдона",
      "genres": "Комедия, криминал",
      "ratings": "КП: 7.4 | IMDb: 7.1",
      "why_match": "Еще один шедевр от режиссера «Брюгге» с Колином Фарреллом, Сэмом Рокуэллом и Вуди Харрельсоном.",
      "plot_hook": "Сценарист-алкоголик втягивается в похищение любимой собачки безумного гангстера.",
      "where_to_watch": "Кинопоиск, Иви, KION"
    }},
    {{
      "title_ru": "Банши Инишерина",
      "title_orig": "The Banshees of Inisherin (2022)",
      "director": "Мартин Макдона",
      "genres": "Драма, комедия",
      "ratings": "КП: 7.5 | IMDb: 7.7",
      "why_match": "Легендарный дуэт Глисон-Фаррелл в пронзительной черной трагикомедии об абсурдном разрыве дружбы.",
      "plot_hook": "На отдаленном ирландском острове один давний друг внезапно заявляет другому, что больше не хочет с ним общаться под угрозой членовредительства.",
      "where_to_watch": "Онлайн-кинотеатры"
    }},
    {{
      "title_ru": "Занесло",
      "title_orig": "Redirected (2014)",
      "director": "Эмилис Веливис",
      "genres": "Боевик, комедия, криминал",
      "ratings": "КП: 7.2 | IMDb: 6.6",
      "why_match": "Угарный криминальный экшен в духе раннего Гая Ричи с Винни Джонсом в главной роли.",
      "plot_hook": "Четверо лондонских грабителей случайно приземляются в дикой восточноевропейской глуши вместо Малайзии.",
      "where_to_watch": "Кинопоиск, Okko, Wink"
    }},
    {{
      "title_ru": "Рок-н-рольщик",
      "title_orig": "RocknRolla (2008)",
      "director": "Гай Ричи",
      "genres": "Криминал, комедия, боевик",
      "ratings": "КП: 7.8 | IMDb: 7.2",
      "why_match": "Британский драйв, рок-н-ролл, русские олигархи, украденная счастливая картина и фирменный юмор.",
      "plot_hook": "Мелкая лондонская банда пытается урвать кусок от миллиардной сделки с недвижимостью.",
      "where_to_watch": "Кинопоиск, Premier, Иви"
    }}
  ],
  "viewing_setup": "🍺 Пинта крафтового стаута или виски со льдом + сочные гренки для максимального погружения в атмосферу."
}}
"""

    resp = await ask_gemini(user_id, context_prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            
            # Apply detected feedback to storage
            detected_fb = data.get("detected_feedback", [])
            for fb in detected_fb:
                title = fb.get("title", "")
                status = fb.get("status", "liked")
                note = fb.get("note", "")
                director = fb.get("director", "")
                genres = fb.get("genres", "")
                year = str(fb.get("year", ""))
                if title:
                    add_or_update_movie_feedback(
                        user_id=user_id,
                        movie_title=title,
                        status=status,
                        note=note,
                        director=director,
                        genres=genres,
                        year=year
                    )
            
            # Update taste profile if present
            new_taste = data.get("new_taste_summary")
            fav_dir = data.get("new_favorite_directors")
            fav_gen = data.get("new_favorite_genres")
            dis_trop = data.get("new_disliked_tropes")
            if new_taste or fav_dir or fav_gen or dis_trop:
                update_user_taste_profile(
                    user_id=user_id,
                    taste_summary=new_taste or taste_summary,
                    favorite_genres=fav_gen,
                    favorite_directors=fav_dir,
                    disliked_tropes=dis_trop
                )

            # Store last recommended movies
            movies = data.get("movies", [])
            if movies:
                set_last_recommended_movies(user_id, movies)

            return data
    except Exception as e:
        logger.error(f"Error parsing cinema matchmaker JSON: {e}")

    # Fallback default
    default_movies = [
        {
            "title_ru": "Джентльмены",
            "title_orig": "The Gentlemen (2019)",
            "director": "Гай Ричи",
            "genres": "Криминал, комедия, боевик",
            "ratings": "КП: 8.6 | IMDb: 7.8",
            "why_match": "Эталонный британский стиль, острые диалоги, динамика и неподражаемый колорит.",
            "plot_hook": "Американский экспат пытается продать свою империю марихуаны в Лондоне, что приводит к войне банд.",
            "where_to_watch": "Кинопоиск, Иви, Okko"
        },
        {
            "title_ru": "Залечь на дно в Брюгге",
            "title_orig": "In Bruges (2008)",
            "director": "Мартин Макдона",
            "genres": "Криминал, драма, черная комедия",
            "ratings": "КП: 7.9 | IMDb: 7.9",
            "why_match": "Культовая черная комедия с философским подтекстом и великолепным актерским дуэтом.",
            "plot_hook": "Два наемных убийцы отправляются переждать шумиху в сказочный бельгийский Брюгге.",
            "where_to_watch": "Кинопоиск, Okko"
        },
        {
            "title_ru": "Большой куш",
            "title_orig": "Snatch (2000)",
            "director": "Гай Ричи",
            "genres": "Криминал, комедия",
            "ratings": "КП: 8.5 | IMDb: 8.2",
            "why_match": "Классика жанра, невероятный саундтрек, яркие персонажи и искрометный юмор.",
            "plot_hook": "В Лондоне переплетаются судьбы похитителей бриллианта, цыганских боксеров и русских бандитов.",
            "where_to_watch": "Кинопоиск, Иви, KION"
        },
        {
            "title_ru": "Карты, деньги, два ствола",
            "title_orig": "Lock, Stock and Two Smoking Barrels (1998)",
            "director": "Гай Ричи",
            "genres": "Криминал, комедия",
            "ratings": "КП: 8.6 | IMDb: 8.1",
            "why_match": "Дебютный шедевр, заложивший основы современного британского криминального кино.",
            "plot_hook": "Четверо парней должны крупную сумму криминальному боссу и решают ограбить соседей-бандитов.",
            "where_to_watch": "Кинопоиск, Okko, Start"
        },
        {
            "title_ru": "Голгофа",
            "title_orig": "Calvary (2014)",
            "director": "Джон Майкл Макдона",
            "genres": "Драма, черная комедия",
            "ratings": "КП: 7.7 | IMDb: 7.4",
            "why_match": "Ирландский сарказм, великолепный Брендан Глисон и глубокие диалоги.",
            "plot_hook": "Священник узнает, что через неделю его убьют, и пытается спасти души жителей городка.",
            "where_to_watch": "Кинопоиск, Иви"
        }
    ]
    set_last_recommended_movies(user_id, default_movies)
    return {
        "thought_process": "🧠 Подобрал 5 эталонных картин под ваш вкус с учетом режиссерского почерка и динамики.",
        "mood_summary": "Кинематографичные шедевры с острыми диалогами и неповторимым стилем",
        "movies": default_movies,
        "viewing_setup": "🍿 Попкорн или любимый крафтовый напиток для вечернего киносеанса."
    }


async def process_quick_rating(user_id: int, movie_index: int, status: str) -> Dict[str, Any]:
    """
    Handles fast 1-click rating for movie #1..#5 from inline buttons.
    """
    last_recommended = get_last_recommended_movies(user_id)
    if not (1 <= movie_index <= len(last_recommended)):
        return {"success": False, "message": "Фильм не найден в текущей подборке."}

    m = last_recommended[movie_index - 1]
    title = m.get("title_ru", m.get("title_orig", f"Фильм #{movie_index}"))
    director = m.get("director", "")
    genres = m.get("genres", "")
    year = ""
    orig = m.get("title_orig", "")
    m_year = re.search(r"\((\d{4})\)", orig)
    if m_year:
        year = m_year.group(1)

    add_or_update_movie_feedback(
        user_id=user_id,
        movie_title=title,
        status=status,
        note=f"Быстрая оценка по рекомендации #{movie_index}",
        director=director,
        genres=genres,
        year=year
    )

    # Trigger quick background taste update
    user_mem = get_user_cinema_memory(user_id)
    taste_prompt = (
        f"Пользователь оценил фильм '{title}' ({genres}, реж. {director}) со статусом '{status}'.\n"
        f"Текущее описание вкуса: '{user_mem.get('taste_summary', '')}'.\n"
        "Сформулируй обновленное краткое (1-2 предложения) описание вкуса пользователя и 2-3 ключевых жанра/режиссера.\n"
        "Верни JSON: {\"taste_summary\": \"...\", \"favorite_genres\": [...], \"favorite_directors\": [...]}"
    )
    try:
        resp = await ask_gemini(user_id, taste_prompt)
        m_json = re.search(r"\{.*\}", resp, re.DOTALL)
        if m_json:
            t_data = json.loads(m_json.group(0))
            update_user_taste_profile(
                user_id=user_id,
                taste_summary=t_data.get("taste_summary", ""),
                favorite_genres=t_data.get("favorite_genres"),
                favorite_directors=t_data.get("favorite_directors")
            )
    except Exception as e:
        logger.warning(f"Error updating quick taste profile: {e}")

    return {
        "success": True,
        "movie_title": title,
        "status": status,
        "director": director
    }
