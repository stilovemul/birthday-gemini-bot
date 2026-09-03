import re
import json
import logging
from typing import Dict, Any, Optional
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
    # 1. First, resolve the best continuous playlist from Yandex.Music
    pl_info = await get_best_yandex_playlist(query_or_vibe, preset_key=preset_key)
    owner = pl_info.get("owner", "yamusic")
    kind = pl_info.get("kind", "1000")
    pl_title = pl_info.get("title", "Плейлист")
    track_count = pl_info.get("track_count", 100)
    pl_url = pl_info.get("url", "https://music.yandex.ru/radio")

    # 2. Fetch the actual first tracks of this real playlist
    real_tracks = await get_playlist_tracks(owner, kind, limit=6)

    data = None
    if real_tracks:
        tracks_formatted = "\n".join([f"{idx}. {t['artist']} — {t['title']}" for idx, t in enumerate(real_tracks, 1)])
        prompt = f"""Ты — персональный музыкальный сомелье и диджей.
Пользователь выбрал вайб: '{query_or_vibe}'.
Мы подобрали для него официальный плейлист Яндекс.Музыки: «{pl_title}» ({track_count} треков).

Вот РЕАЛЬНЫЙ трек-лист из этого плейлиста:
{tracks_formatted}

Напиши атмосферную сомелье-презентацию этого плейлиста и краткий яркий комментарий к каждому из этих {len(real_tracks)} треков (почему трек задает идеальный ритм и настроение).

Верни ответ СТРОГО в формате JSON:
{{
  "playlist_title": "Яркое эстетичное название сета",
  "vibe_description": "Описание настроения, атмосферы и жанров (2-3 предложения)",
  "tracks": [
    {{"artist": "{real_tracks[0]['artist']}", "title": "{real_tracks[0]['title']}", "why_match": "Краткое сомелье-описание трека"}},
    ...
  ],
  "ideal_volume": "Совет по прослушиванию (наушники, авто, фоном)"
}}
"""
        try:
            resp = await ask_gemini(user_id, prompt)
            m = re.search(r"\{.*\}", resp, re.DOTALL)
            if m:
                parsed = json.loads(m.group(0))
                # Merge with real_tracks to guarantee track names & URLs
                parsed_tracks = parsed.get("tracks", [])
                final_tracks = []
                for idx, rt in enumerate(real_tracks):
                    why = "Задает отличное настроение и погружает в атмосферу."
                    if idx < len(parsed_tracks):
                        why = parsed_tracks[idx].get("why_match", why)
                    final_tracks.append({
                        "artist": rt["artist"],
                        "title": rt["title"],
                        "track_url": rt.get("track_url", ""),
                        "why_match": why
                    })
                data = {
                    "playlist_title": parsed.get("playlist_title", pl_title),
                    "vibe_description": parsed.get("vibe_description", "Качественная музыка под настроение."),
                    "tracks": final_tracks,
                    "ideal_volume": parsed.get("ideal_volume", "🎧 В наушниках для полного погружения.")
                }
        except Exception as e:
            logger.error(f"Error calling gemini for real tracks: {e}")

    # Fallback if no real tracks or Gemini error
    if not data:
        if real_tracks:
            final_tracks = [{
                "artist": rt["artist"],
                "title": rt["title"],
                "track_url": rt.get("track_url", ""),
                "why_match": "Идеально задает настроение сета."
            } for rt in real_tracks]
        else:
            final_tracks = [
                {"artist": "Tycho", "title": "Awake", "track_url": "", "why_match": "Чистая концентрация и ясность ума."},
                {"artist": "Bonobo", "title": "Cirrus", "track_url": "", "why_match": "Ритмичный инструментал для фокуса."}
            ]

        data = {
            "playlist_title": pl_title,
            "vibe_description": "Качественная непрерывная подборка под ваше настроение.",
            "tracks": final_tracks,
            "ideal_volume": "🎧 В наушниках фоном для полного погружения."
        }

    data["continuous_playlist_url"] = pl_url
    data["continuous_playlist_title"] = pl_title
    data["continuous_playlist_tracks_count"] = track_count
    data["yandex_music_url"] = pl_url

    return data
