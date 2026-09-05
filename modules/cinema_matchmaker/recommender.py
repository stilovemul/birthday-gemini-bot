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
    update_user_taste_profile,
    mark_all_last_recommended_as_watched,
    get_all_excluded_titles,
    get_active_search_context,
    set_active_search_context,
    get_dialog_history,
    append_dialog_turn,
    clean_title_str
)
from modules.cinema_matchmaker.catalog import get_curated_fallback

logger = logging.getLogger("CinemaMatchmaker")


def detect_query_intent(query: str, current_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses natural language triggers for:
    - Marking previous batch as watched ("всё смотрел", "все это видел", "уже смотрел")
    - Asking for next/other batch ("еще", "давай другое", "следующие")
    - Detecting format (сериал vs фильм) and country (Россия vs Зарубежные).
    """
    q_low = query.lower()
    
    # 1. Check if user watched all of the previous recommendations
    watched_all_triggers = [
        "все смотрел", "всё смотрел", "смотрел все", "смотрел всё",
        "все это смотрел", "всё это смотрел", "все эти смотрел", "всё это видел",
        "все видел", "всё видел", "я все это смотрел", "я всё это смотрел",
        "уже все смотрел", "уже всё смотрел", "все из этого смотрел", "всё из этого смотрел",
        "все эти видел", "всё эти видел", "смотрели всё", "смотрели все"
    ]
    is_watched_all = any(t in q_low for t in watched_all_triggers)
    
    # 2. Check if user is asking for more / another batch
    more_triggers = [
        "давай другое", "давай другой", "что-то другое", "еще", "ещё",
        "покажи еще", "покажи ещё", "следующие", "другие", "еще варианты", "ещё варианты",
        "дай еще", "дай ещё", "дальше"
    ]
    is_more = any(t in q_low for t in more_triggers)
    
    # 3. Detect format
    format_type = current_context.get("format", "любой")
    if any(w in q_low for w in ["сериал", "сериалы", "сериальчик", "многосерийный"]):
        format_type = "сериал"
    elif any(w in q_low for w in ["фильм", "фильмы", "кино", "полный метр", "киношка"]):
        format_type = "фильм"

    # 4. Detect country / origin
    country = current_context.get("country", "любая")
    if any(w in q_low for w in ["русск", "росси", "наш сериал", "наши сериал", "отечественн", "русский", "русские", "наше кино"]):
        country = "Россия"
    elif any(w in q_low for w in ["зарубеж", "иностран", "американск", "сша", "европейск", "корейск", "британск", "английск"]):
        country = "Зарубежные"

    return {
        "is_watched_all": is_watched_all,
        "is_more": is_more,
        "format": format_type,
        "country": country
    }


async def recommend_movies(user_id: int, query: str, force_new_recommendation: bool = False) -> Dict[str, Any]:
    """
    Cognitive AI Film Sommelier with Thought Process, Dialog Memory, and Dynamic Context Pinning.
    Never loops, strictly remembers all shown and watched titles, respects user format and country!
    """
    user_mem = get_user_cinema_memory(user_id)
    current_context = get_active_search_context(user_id)
    dialog_hist = get_dialog_history(user_id)
    
    # Detect intent
    intent = detect_query_intent(query, current_context)
    marked_watched_titles: List[str] = []
    
    if intent["is_watched_all"]:
        marked_watched_titles = mark_all_last_recommended_as_watched(user_id)
        logger.info(f"User {user_id} marked all last recommended movies as watched: {marked_watched_titles}")
        # Refresh user_mem after marking watched
        user_mem = get_user_cinema_memory(user_id)

    # Update active search context with detected format/country and current query
    new_context = {
        "format": intent["format"] if intent["format"] != "любой" else current_context.get("format", "любой"),
        "country": intent["country"] if intent["country"] != "любая" else current_context.get("country", "любая"),
        "last_query": query
    }
    set_active_search_context(user_id, new_context)

    watched: List[Dict[str, Any]] = user_mem.get("watched_movies", [])
    taste_summary: str = user_mem.get("taste_summary", "")
    favorite_genres: List[str] = user_mem.get("favorite_genres", [])
    favorite_directors: List[str] = user_mem.get("favorite_directors", [])
    disliked_tropes: List[str] = user_mem.get("disliked_tropes", [])
    all_excluded = get_all_excluded_titles(user_id)
    last_recommended = get_last_recommended_movies(user_id)

    liked_titles = [f"{w['title']}" + (f" ({w['director']})" if w.get('director') else "") + (f" [«{w['note']}»]" if w.get('note') else "") for w in watched if w.get("status") == "liked"]
    disliked_titles = [f"{w['title']}" + (f" ({w['director']})" if w.get('director') else "") + (f" [«{w['note']}»]" if w.get('note') else "") for w in watched if w.get("status") == "disliked"]
    watched_only_titles = [f"{w['title']}" for w in watched if w.get("status") == "watched"]

    # Dialog history representation
    dialog_lines = []
    for turn in dialog_hist[-6:]:
        role_label = "Пользователь" if turn.get("role") == "user" else "Киносомелье"
        dialog_lines.append(f"{role_label}: {turn.get('text')}")
    dialog_str = "\n".join(dialog_lines) if dialog_lines else "Диалог только начался"

    # Excluded titles string (top 100 most recent for prompt compactness)
    excluded_str = ", ".join(all_excluded[-100:]) if all_excluded else "Пока нет исключений"

    # Specific instruction about format and country
    target_format_instruction = ""
    if new_context["country"] == "Россия" and new_context["format"] == "сериал":
        target_format_instruction = "⚠️ СТРОЖАЙШЕЕ ТРЕБОВАНИЕ: Пользователь ищет РОССИЙСКИЙ СЕРИАЛ (Россия). Все 5 рекомендаций должны быть ТОЛЬКО российскими сериалами! Категорически запрещено предлагать зарубежные фильмы или фильмы Гая Ричи!"
    elif new_context["country"] == "Россия":
        target_format_instruction = "⚠️ ТРЕБОВАНИЕ: Пользователь ищет РОССИЙСКОЕ кино/сериалы (Россия). Все 5 рекомендаций должны быть отечественного производства."
    elif new_context["format"] == "сериал":
        target_format_instruction = "⚠️ ТРЕБОВАНИЕ: Пользователь ищет СЕРИАЛ (многосерийный формат). Не предлагай полнометражные фильмы."
    elif new_context["format"] == "фильм":
        target_format_instruction = "⚠️ ТРЕБОВАНИЕ: Пользователь ищет ПОЛНОМЕТРАЖНЫЙ ФИЛЬМ на вечер."

    special_note = ""
    if marked_watched_titles:
        special_note = f"\nВНИМАНИЕ: Пользователь только что сообщил, что ВСЕ предыдущие рекомендации ({', '.join(marked_watched_titles)}) он УЖЕ СМОТРЕЛ. Они добавлены в черный список. Подбери 5 СОВЕРШЕННО НОВЫХ вариантов, сохранив текущий вектор поиска!\n"

    context_prompt = f"""Ты — профессиональный кинокритик, эксперт киноискусства и персональный AI-Киносомелье с непрерывной памятью и когнитивным интеллектом.

=== ИСТОРИЯ ПРЕДЫДУЩЕГО ДИАЛОГА В СЕССИИ ===
{dialog_str}
==============================================

=== ТЕКУЩИЙ ЦЕЛЕВОЙ ФОРМАТ ПОИСКА ===
• Формат: {new_context['format']}
• Страна / Регион: {new_context['country']}
{target_format_instruction}
======================================

=== ПРОФИЛЬ ВКУСА И ПАМЯТЬ ПОЛЬЗОВАТЕЛЯ ===
• Сформированный вкус: {taste_summary or 'Формируется'}
• Любимые режиссеры/шоураннеры: {", ".join(favorite_directors) if favorite_directors else 'Не выделены'}
• Любимые жанры/стили: {", ".join(favorite_genres) if favorite_genres else 'Не выделены'}
• Избегать: {", ".join(disliked_tropes) if disliked_tropes else 'Нет'}
• 👍 ПОНРАВИЛИСЬ (просмотрено): {"; ".join(liked_titles[-25:]) if liked_titles else 'Пока нет'}
• 👎 НЕ ПОНРАВИЛИСЬ: {"; ".join(disliked_titles[-20:]) if disliked_titles else 'Пока нет'}
• 👀 ПРОСМОТРЕНО (всего {len(all_excluded)} в черном списке): {"; ".join(watched_only_titles[-20:]) if watched_only_titles else 'Нет'}
==========================================

🚫 СПИСОК ИСКЛЮЧЕНИЙ (СТРОЖАЙШИЙ ЗАПРЕТ! НИКОГДА НЕ ПРЕДЛАГАЙ ЭТИ КАРТИНЫ):
{excluded_str}
=======================================================================
{special_note}
ВХОДЯЩЕЕ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ: «{query}»

ТВОЙ МЫСЛИТЕЛЬНЫЙ ПРОЦЕСС И ЗАДАЧИ:
1. [АНАЛИЗ СООБЩЕНИЯ И ОБРАТНОЙ СВЯЗИ]:
   - Упоминает ли пользователь конкретные фильмы/сериалы, которые он сейчас смотрит или смотрел ранее с положительной или отрицательной оценкой (например: «мы сейчас смотрим ЮЗЗЗ, очень нравится, еще смотрели Капельник»)?
   - Если ДА: извлеки их в массив 'detected_feedback' (статус 'liked' / 'disliked' / 'watched'), укажи режиссера и жанр, чтобы бот запомнил их навсегда.
   - Сформулируй блок 'thought_process' (живой человечный комментарий кинокритика: что бот зафиксировал, как это уточняет поиск и почему подобраны именно следующие 5 картин).
   - Сформулируй 'new_taste_summary', дополни 'new_favorite_directors', 'new_favorite_genres', 'new_disliked_tropes'.

2. [ПОДБОР 5 ТОП-КАРТИН]:
   - Подбери РОВНО 5 великолепных, неизбитых, качественных картин строго под активный запрос пользователя ({new_context['country']} / {new_context['format']})!
   - КАТЕГОРИЧЕСКИЙ ЗАПРЕТ: Ни одна из 5 рекомендаций не должна быть из списка исключений!
   - Если пользователь ищет российский сериал — выдай 5 ТОПОВЫХ российских сериалов (например: «Лада Голд», «1703», «Черная весна», «Смычок», «13 клиническая», «Пингвины моей мамы», «Трасса», «Престиж», «Лихие», «Алиса не может ждать» и др.), объясняя попадание в вайб любимых сериалов пользователя.
   - В поле 'why_match' четко обоснуй попадание в атмосферу, юмор или сюжетные линии названных пользователем картин.
   - Укажи реальные рейтинги Кинопоиска (КП) и IMDb.
   - Укажи, где легально смотреть в РФ (Кинопоиск, Иви, Okko, Start, Premier, KION, Wink).
   - Составь 'viewing_setup' (подходящий напиток, закуска, атмосфера).

Верни ответ СТРОГО в формате JSON:
{{
  "thought_process": "🧠 Зафиксировал в памяти: вы смотрите «...» (👍) и вам понравился «...» (👍). Понял ваш запрос на крепкие российские сериалы с живыми диалогами, драйвом и отличным кастом. Исключил все ранее просмотренные картины и подобрал 5 свежих сериалов в том же духе:",
  "detected_feedback": [
    {{
      "title": "Название сериала",
      "status": "liked",
      "director": "Режиссер",
      "genres": "Жанры",
      "year": "2023",
      "note": "Понравился"
    }}
  ],
  "new_taste_summary": "Описание вкуса...",
  "new_favorite_directors": ["Имя"],
  "new_favorite_genres": ["Жанр"],
  "new_disliked_tropes": ["Троп"],
  "mood_summary": "Краткий вайб подборки",
  "movies": [
    {{
      "title_ru": "Название на русском",
      "title_orig": "Название (Год)",
      "director": "Режиссер / Шоураннер",
      "genres": "Жанры (Сериал / Фильм)",
      "ratings": "КП: 7.8 | IMDb: 7.4",
      "why_match": "Почему именно это понравится пользователю по сравнению с его референсами...",
      "plot_hook": "Интригующая завязка сюжета...",
      "where_to_watch": "Start, Кинопоиск, Okko"
    }}
  ],
  "viewing_setup": "🍿 Что взять к просмотру..."
}}
"""

    resp = await ask_gemini(user_id, context_prompt)
    
    # Save dialog turn
    append_dialog_turn(user_id, "user", query)

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

            # Store last recommended movies and add to shown history
            movies = data.get("movies", [])
            if movies and len(movies) >= 1:
                # Filter out any accidentally repeated titles
                fresh_movies = []
                for mov in movies:
                    m_title = clean_title_str(mov.get("title_ru") or mov.get("title_orig") or "")
                    if m_title:
                        fresh_movies.append(mov)
                
                # If Gemini returned fewer than 5, supplement from curated catalog
                if len(fresh_movies) < 5:
                    supplements = get_curated_fallback(
                        format_type=new_context.get("format", "любой"),
                        country=new_context.get("country", "любая"),
                        excluded_titles=get_all_excluded_titles(user_id)
                    )
                    for sup in supplements:
                        if len(fresh_movies) >= 5:
                            break
                        if clean_title_str(sup.get("title_ru", "")) not in [clean_title_str(x.get("title_ru", "")) for x in fresh_movies]:
                            fresh_movies.append(sup)

                data["movies"] = fresh_movies[:5]
                set_last_recommended_movies(user_id, data["movies"])
                
                # Save assistant dialog summary
                summary_titles = ", ".join([x.get("title_ru", "") for x in data["movies"]])
                append_dialog_turn(user_id, "assistant", f"Рекомендовал 5 картин: {summary_titles}")
                return data
    except Exception as e:
        logger.error(f"Error parsing cinema matchmaker JSON response: {e}")

    # Intelligent curated fallback matching user's active context
    excluded = get_all_excluded_titles(user_id)
    fallback_movies = get_curated_fallback(
        format_type=new_context.get("format", "любой"),
        country=new_context.get("country", "любая"),
        excluded_titles=excluded
    )
    set_last_recommended_movies(user_id, fallback_movies)
    
    thought_msg = "🧠 Учел ваши пожелания и исключил все ранее просмотренные картины. "
    if new_context["country"] == "Россия" and new_context["format"] == "сериал":
        thought_msg += "Подобрал 5 отличных российских сериалов с высоким рейтингом и захватывающим сюжетом:"
    else:
        thought_msg += "Подобрал 5 рейтинговых картин с яркими персонажами и отличным сценарием:"

    summary_titles = ", ".join([x.get("title_ru", "") for x in fallback_movies])
    append_dialog_turn(user_id, "assistant", f"Рекомендовал 5 картин: {summary_titles}")

    return {
        "thought_process": thought_msg,
        "mood_summary": f"Качественные {new_context.get('country', '')} {new_context.get('format', 'фильмы и сериалы')}".strip(),
        "movies": fallback_movies,
        "viewing_setup": "🍿 Отличная компания и любимые напитки для идеального киносеанса."
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
    clean_t = clean_title_str(title)
    director = m.get("director", "")
    genres = m.get("genres", "")
    year = ""
    orig = m.get("title_orig", "")
    m_year = re.search(r"\((\d{4})\)", orig)
    if m_year:
        year = m_year.group(1)

    add_or_update_movie_feedback(
        user_id=user_id,
        movie_title=clean_t,
        status=status,
        note=f"Оценка по рекомендации #{movie_index}",
        director=director,
        genres=genres,
        year=year
    )

    # Quick background taste update
    user_mem = get_user_cinema_memory(user_id)
    taste_prompt = (
        f"Пользователь оценил картину '{clean_t}' ({genres}, реж. {director}) со статусом '{status}'.\n"
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
        "movie_title": clean_t,
        "status": status,
        "director": director
    }
