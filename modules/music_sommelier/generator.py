import re
import json
import logging
from typing import Dict, Any, Optional, List
from core.gemini import ask_gemini
from modules.music_sommelier.yandex_api import (
    get_best_yandex_playlist,
    get_playlist_tracks
)

logger = logging.getLogger("MusicSommelier")

async def generate_music_playlist(
    user_id: int,
    query_or_vibe: str,
    preset_key: Optional[str] = None
) -> Dict[str, Any]:
    # 1. Ask Gemini to analyze intent and extract keywords + preliminary vibe
    intent_prompt = f"""Ты — музыкальный эксперт и сомелье.
Пользователь написал запрос: '{query_or_vibe}'.

Определи:
1. "search_keywords": 3-4 лучших коротких поисковых фразы для каталога Яндекс.Музыки (на русском и английском), отражающие активность, настроение или жанр. Например, для 'составь плейлист под уборку дома' -> ["Уборка дома", "Музыка для уборки", "Уборка", "Cleaning Pop"].
2. "playlist_title": Яркое название сета (например: «Генеральная уборка: Максимальный драйв», «Sunset Chill», «Energy Run»).
3. "vibe_description": Описание настроения, темпа и жанров (2-3 предложения).
4. "ideal_volume": Рекомендация по звуку (в наушниках, на домашней акустике, в авто).

Ответь СТРОГО в формате JSON:
{{
  "search_keywords": ["Уборка дома", "Музыка для уборки", "Уборка"],
  "playlist_title": "Генеральная уборка: Полный заряд",
  "vibe_description": "Бодрый танцевальный поп, позитивный фанк и диско для легкой и энергичной уборки.",
  "ideal_volume": "🔊 На домашней колонке или акустике для наполнения дома энергией."
}}
"""
    parsed_intent = {}
    try:
        resp = await ask_gemini(user_id, intent_prompt)
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            parsed_intent = json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing intent with gemini: {e}")

    extra_queries: List[str] = parsed_intent.get("search_keywords", [])
    pl_title = parsed_intent.get("playlist_title", "Атмосферный музыкальный сет")
    vibe_desc = parsed_intent.get("vibe_description", "Качественная непрерывная музыка под ваше занятие.")
    ideal_volume = parsed_intent.get("ideal_volume", "🎧 В наушниках для полного погружения.")

    # 2. Resolve best continuous playlist from Yandex.Music
    pl_info = await get_best_yandex_playlist(
        query_or_vibe,
        preset_key=preset_key,
        extra_queries=extra_queries
    )
    owner = pl_info.get("owner", "yamusic")
    kind = pl_info.get("kind", "1000")
    found_title = pl_info.get("title", pl_title)
    track_count = pl_info.get("track_count", 100)
    pl_url = pl_info.get("url", "https://music.yandex.ru/radio")

    # 3. Fetch real tracks of the discovered playlist
    real_tracks = await get_playlist_tracks(owner, kind, limit=6)

    # 4. Generate commentary for the actual tracks
    final_tracks = []
    if real_tracks:
        tracks_formatted = "\n".join([f"{idx}. {t['artist']} — {t['title']}" for idx, t in enumerate(real_tracks, 1)])
        commentary_prompt = f"""Ты — музыкальный сомелье.
Запрос пользователя: '{query_or_vibe}'.
Мы подобрали плейлист «{found_title}» ({track_count} треков).
Вот первые треки:
{tracks_formatted}

Напиши для каждого трека короткий сомелье-комментарий (1 предложение), почему он идеально подходит под '{query_or_vibe}'.

Верни ответ СТРОГО в JSON:
{{
  "tracks": [
    {{"artist": "{real_tracks[0]['artist']}", "title": "{real_tracks[0]['title']}", "why_match": "Краткое пояснение"}},
    ...
  ]
}}
"""
        try:
            c_resp = await ask_gemini(user_id, commentary_prompt)
            cm = re.search(r"\{.*\}", c_resp, re.DOTALL)
            if cm:
                c_data = json.loads(cm.group(0))
                c_tracks = c_data.get("tracks", [])
                for idx, rt in enumerate(real_tracks):
                    why = "Задает нужный темп и заряжает энергией."
                    if idx < len(c_tracks):
                        why = c_tracks[idx].get("why_match", why)
                    final_tracks.append({
                        "artist": rt["artist"],
                        "title": rt["title"],
                        "track_url": rt.get("track_url", ""),
                        "why_match": why
                    })
        except Exception as e:
            logger.error(f"Error generating track commentary: {e}")

    if not final_tracks:
        if real_tracks:
            final_tracks = [{
                "artist": rt["artist"],
                "title": rt["title"],
                "track_url": rt.get("track_url", ""),
                "why_match": "Идеально задает настроение и ритм."
            } for rt in real_tracks]
        else:
            # Fallback if no playlist found: generate real tracks matching the prompt
            gen_prompt = f"""Ты — музыкальный сомелье.
Пользователь просит музыку: '{query_or_vibe}'.
Предложи 5-6 РЕАЛЬНЫХ популярных треков, которые идеально подходят под этот запрос.

Верни JSON:
{{
  "tracks": [
    {{"artist": "Исполнитель", "title": "Название", "why_match": "Почему подходит"}}
  ]
}}
"""
            try:
                g_resp = await ask_gemini(user_id, gen_prompt)
                gm = re.search(r"\{.*\}", g_resp, re.DOTALL)
                if gm:
                    g_data = json.loads(gm.group(0))
                    for t in g_data.get("tracks", []):
                        final_tracks.append({
                            "artist": t.get("artist", ""),
                            "title": t.get("title", ""),
                            "track_url": "",
                            "why_match": t.get("why_match", "Отлично подходит под настроение.")
                        })
            except Exception:
                pass

    return {
        "playlist_title": pl_title if pl_title and pl_title != "Плейлист" else found_title,
        "vibe_description": vibe_desc,
        "tracks": final_tracks,
        "ideal_volume": ideal_volume,
        "continuous_playlist_url": pl_url,
        "continuous_playlist_title": found_title,
        "continuous_playlist_tracks_count": track_count,
        "yandex_music_url": pl_url
    }
