import re
import json
import logging
from typing import Dict, Any, Optional
from core.gemini import ask_gemini
from modules.music_sommelier.yandex_api import (
    get_best_yandex_playlist,
    enrich_tracks_with_urls
)

logger = logging.getLogger("MusicSommelier")

async def generate_music_playlist(
    user_id: int,
    query_or_vibe: str,
    preset_key: Optional[str] = None
) -> Dict[str, Any]:
    prompt = f"""Ты — персональный музыкальный сомелье и диджей.
Настроение / Ситуация пользователя / Вайб: '{query_or_vibe}'

Сгенерируй атмосферный сет из 5-6 реально существующих треков, идеально создающих этот вайб (ночная езда по КАД/ЗСД, фокус на работе, тренировка, шашлык на даче, вечерний чилл).
Выбирай известные, высоко оцененные треки реальных исполнителей, которые есть в стримингах (Яндекс.Музыка).

СТРУКТУРА JSON:
1. "playlist_title": Яркое название плейлиста (например: «Midnight Drive: Неоновый ЗСД», «Deep Focus: Архитектор кода», «Sunset Lounge»)
2. "vibe_description": Описание настроения и музыкальных жанров (Lo-Fi, Synthwave, Ambient, Phonk, Deep House, Indie Rock)
3. "yandex_music_query": Оптимальный поисковый запрос жанра/стиля для Яндекс.Музыки (например: "Lo-Fi концентрация", "Synthwave Night Drive", "Hard Rock Workout", "Блюз рок")
4. "tracks": Список 5-6 треков:
   - "artist": Точное имя исполнителя
   - "title": Точное название трека
   - "why_match": Почему трек идеально бьет в настроение
5. "ideal_volume": Совет по прослушиванию (в наушниках, в авто с сабвуфером, фоном).

Верни ответ СТРОГО в формате JSON:
{{
  "playlist_title": "Deep Focus: Архитектор кода",
  "vibe_description": "Атмосферный Lo-Fi, глубокий Ambient и минималистичный инструментал для продуктивной работы.",
  "yandex_music_query": "Lo-Fi концентрация",
  "tracks": [
    {{"artist": "L'Indecis", "title": "Soulful", "why_match": "Мягкий ритм, помогающий войти в состояние потока."}},
    {{"artist": "Tycho", "title": "Awake", "why_match": "Энергичный, но ненавязчивый инструментал для чистого ума."}}
  ],
  "ideal_volume": "🎧 В качественных наушниках фоном для полного погружения."
}}
"""
    data = None
    try:
        resp = await ask_gemini(user_id, prompt)
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error calling gemini or parsing json: {e}")

    if not data:
        data = {
            "playlist_title": "Атмосферный музыкальный сет",
            "vibe_description": "Качественная музыка для отличного настроения и продуктивности.",
            "yandex_music_query": query_or_vibe,
            "tracks": [
                {"artist": "Hans Zimmer", "title": "Time", "why_match": "Эпическая глубина и масштаб."},
                {"artist": "Tycho", "title": "Awake", "why_match": "Глубокая концентрация и ясность."}
            ],
            "ideal_volume": "🎧 В наушниках для полного погружения."
        }

    # 1. Resolve the best continuous non-stop playlist from Yandex Music
    ym_query = data.get("yandex_music_query") or query_or_vibe
    try:
        pl_info = await get_best_yandex_playlist(ym_query, preset_key=preset_key)
        data["continuous_playlist_url"] = pl_info.get("url", "https://music.yandex.ru/radio")
        data["continuous_playlist_title"] = pl_info.get("title", "Плейлист")
        data["continuous_playlist_tracks_count"] = pl_info.get("track_count", 0)
        data["yandex_music_url"] = data["continuous_playlist_url"]
    except Exception as e:
        logger.error(f"Error resolving continuous playlist: {e}")
        data["continuous_playlist_url"] = "https://music.yandex.ru/radio"
        data["continuous_playlist_title"] = "Моя Волна (Поток)"
        data["continuous_playlist_tracks_count"] = 100
        data["yandex_music_url"] = data["continuous_playlist_url"]

    # 2. Enrich tracks with direct Yandex Music URLs in parallel
    try:
        tracks = data.get("tracks", [])
        if tracks:
            data["tracks"] = await enrich_tracks_with_urls(tracks)
    except Exception as e:
        logger.error(f"Error enriching tracks with urls: {e}")

    return data
