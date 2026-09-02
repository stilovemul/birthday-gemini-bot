import re
import json
import urllib.parse
import logging
from typing import Dict, Any
from core.gemini import ask_gemini

logger = logging.getLogger("MusicSommelier")

async def generate_music_playlist(user_id: int, query_or_vibe: str) -> Dict[str, Any]:
    prompt = f"""Ты — персональный музыкальный сомелье и диджей.
Настроение / Ситуация пользователя / Вайб: '{query_or_vibe}'

Сгенерируй атмосферный плейлист из 5-6 треков, идеально создающих этот вайб (ночная езда по КАД/ЗСД, фокус на работе, тренировка, шашлык на даче, вечерний чилл).

СТРУКТУРА JSON:
1. "playlist_title": Яркое название плейлиста (например: «Midnight Drive: Неоновый ЗСД», «Deep Focus: Чистый код», «Sunset Lounge»)
2. "vibe_description": Описание настроения и музыкальных жанров (Phonk, Synthwave, Deep House, Indie Rock, Lo-Fi)
3. "yandex_music_query": Оптимальный поисковый запрос для Яндекс.Музыки (например: "Synthwave night drive", "Deep House chill", "Indie rock acoustic")
4. "tracks": Список 5-6 треков:
   - "artist": Исполнитель
   - "title": Название трека
   - "why_match": Почему идеально бьет в настроение
5. "ideal_volume": Совет по прослушиванию (в наушниках, в авто с сабвуфером, фоном).

Верни ответ СТРОГО в формате JSON:
{{
  "playlist_title": "Midnight Run: Ночной прострел по ЗСД",
  "vibe_description": "Кинематографичный Synthwave, Dark Disco и плотный Deep House для ночной трассы с огнями города.",
  "yandex_music_query": "Synthwave Night Drive",
  "tracks": [
    {{"artist": "Kavinsky", "title": "Nightcall", "why_match": "Культовая классика ночной езды и неоновой эстетики."}},
    {{"artist": "The Weeknd", "title": "Blinding Lights", "why_match": "Мощный ретровейв-ритм и динамика."}}
  ],
  "ideal_volume": "🔊 В авто на хорошей громкости под огни мостов и ночного залива."
}}
"""
    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            ym_q = data.get("yandex_music_query", data.get("playlist_title", "Music"))
            encoded = urllib.parse.quote_plus(ym_q)
            data["yandex_music_url"] = f"https://music.yandex.ru/search?text={encoded}"
            return data
    except Exception as e:
        logger.error(f"Error parsing music json: {e}")

    return {
        "playlist_title": "Атмосферный музыкальный сет",
        "vibe_description": "Качественная музыка для отличного настроения.",
        "yandex_music_query": "Top Chill Vibes",
        "yandex_music_url": "https://music.yandex.ru",
        "tracks": [
            {"artist": "Hans Zimmer", "title": "Time", "why_match": "Эпическая глубина и масштаб."}
        ],
        "ideal_volume": "В наушниках для полного погружения."
    }
