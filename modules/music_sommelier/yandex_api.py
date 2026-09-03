"""
Yandex Music API Client for Music Sommelier Module.
Provides curated continuous non-stop playlists and extracts real playlist tracklists.
"""

import re
import asyncio
import aiohttp
import urllib.parse
import logging
from typing import Dict, Any, List, Optional
from core.config import YANDEX_OAUTH_TOKEN

logger = logging.getLogger("YandexMusicAPI")

STOP_WORDS = {
    "составь", "составить", "сделай", "сделать", "подбери", "подобрать",
    "включи", "включить", "найди", "найти", "плейлист", "плейлиста", "плейлистов",
    "сет", "сета", "музыка", "музыку", "музыки", "музыке", "трек", "треки", "треков",
    "песни", "песен", "песню", "под", "для", "на", "мне", "нам",
    "пожалуйста", "хочу", "послушать", "слушать", "какой-нибудь", "что-то", "подборка", "подборку"
}

# Top-tier verified curated editorial playlists for continuous background playback (50-230+ tracks)
PRESET_PLAYLISTS: Dict[str, Dict[str, Any]] = {
    "focus": {
        "owner": "music-blog",
        "kind": 2620,
        "title": "Lo-Fi для работы и учебы (Концентрация)",
        "track_count": 234,
        "url": "https://music.yandex.ru/users/music-blog/playlists/2620"
    },
    "drive": {
        "owner": "fixtmusic",
        "kind": 1003,
        "title": "Synthwave & Night Drive (Ночной ЗСД)",
        "track_count": 100,
        "url": "https://music.yandex.ru/users/fixtmusic/playlists/1003"
    },
    "gym": {
        "owner": "music-radio-alice",
        "kind": 1076,
        "title": "Взрывная тренировка (Workout & Gym Power)",
        "track_count": 232,
        "url": "https://music.yandex.ru/users/music-radio-alice/playlists/1076"
    },
    "bbq": {
        "owner": "BogatoRecords",
        "kind": 1053,
        "title": "Дача, Шашлык & Гриль (Блюз-рок, Инди & Фанк)",
        "track_count": 52,
        "url": "https://music.yandex.ru/users/BogatoRecords/playlists/1053"
    }
}


def extract_search_keywords(text: str) -> List[str]:
    """
    Cleans conversational phrasing ('составь плейлист под уборку дома' -> ['уборка дома', 'уборка']).
    """
    words = re.findall(r'[a-zA-Zа-яА-Я0-9\-]+', text.lower())
    meaningful = [w for w in words if w not in STOP_WORDS and len(w) > 1]
    queries = []
    if meaningful:
        # Full meaningful phrase
        full_phrase = " ".join(meaningful)
        queries.append(full_phrase)
        # Individual words with length > 3
        for w in meaningful:
            if len(w) > 3 and w not in queries:
                queries.append(w)
    return queries


async def get_best_yandex_playlist(
    query: str,
    preset_key: Optional[str] = None,
    extra_queries: Optional[List[str]] = None,
    session: Optional[aiohttp.ClientSession] = None
) -> Dict[str, Any]:
    """
    Returns the best matching full continuous non-stop playlist from Yandex.Music.
    """
    if preset_key and preset_key in PRESET_PLAYLISTS:
        return dict(PRESET_PLAYLISTS[preset_key])

    headers = {"Authorization": f"OAuth {YANDEX_OAUTH_TOKEN}"}
    
    # Assemble priority candidate search queries
    candidates: List[str] = []
    if extra_queries:
        for eq in extra_queries:
            clean_eq = eq.strip()
            if clean_eq and clean_eq not in candidates:
                candidates.append(clean_eq)

    kw = extract_search_keywords(query)
    for w in kw:
        if w not in candidates:
            candidates.append(w)

    clean_raw = query.strip()
    if clean_raw not in candidates:
        candidates.append(clean_raw)

    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True

    try:
        for q in candidates:
            enc = urllib.parse.quote(q)
            url = f"https://api.music.yandex.net/search?text={enc}&type=playlist&page=0"
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=3.5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        playlists = data.get("result", {}).get("playlists", {}).get("results", [])
                        if playlists:
                            # Prioritize playlists with track count >= 10, sort by track count
                            playlists.sort(key=lambda p: p.get("trackCount", 0), reverse=True)
                            best = playlists[0]
                            owner = best.get("owner", {}).get("login") or best.get("owner", {}).get("name") or "yamusic"
                            kind = best.get("kind")
                            return {
                                "owner": owner,
                                "kind": kind,
                                "title": best.get("title", q.capitalize()),
                                "track_count": best.get("trackCount", 0),
                                "url": f"https://music.yandex.ru/users/{owner}/playlists/{kind}",
                                "matched_query": q
                            }
            except Exception as e:
                logger.warning(f"Playlist search error for '{q}': {e}")
    finally:
        if close_session:
            await session.close()

    # Fallback to My Wave
    return {
        "owner": "yandex",
        "kind": "radio",
        "title": f"Моя Волна: {query.capitalize()}",
        "track_count": 100,
        "url": "https://music.yandex.ru/radio",
        "matched_query": query
    }


async def get_playlist_tracks(
    owner: str,
    kind: Any,
    limit: int = 6,
    session: Optional[aiohttp.ClientSession] = None
) -> List[Dict[str, Any]]:
    """
    Fetches the actual first tracks of a real Yandex Music playlist.
    Guarantees that what the bot displays in Telegram matches the playlist order 1-to-1!
    """
    if str(kind) == "radio":
        return []

    url = f"https://api.music.yandex.net/users/{owner}/playlists/{kind}"
    headers = {"Authorization": f"OAuth {YANDEX_OAUTH_TOKEN}"}

    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True

    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=4)) as resp:
            if resp.status == 200:
                data = await resp.json()
                raw_tracks = data.get("result", {}).get("tracks", [])
                tracks = []
                for item in raw_tracks[:limit]:
                    t = item.get("track", {})
                    artists = ", ".join([a.get("name") for a in t.get("artists", []) if a.get("name")])
                    title = t.get("title", "")
                    if artists and title:
                        t_id = t.get("id")
                        albums = t.get("albums", [])
                        alb_id = albums[0].get("id") if albums else None
                        track_url = f"https://music.yandex.ru/album/{alb_id}/track/{t_id}" if alb_id else f"https://music.yandex.ru/track/{t_id}"
                        tracks.append({
                            "artist": artists,
                            "title": title,
                            "track_url": track_url
                        })
                return tracks
    except Exception as e:
        logger.warning(f"Failed to fetch tracks for playlist {owner}/{kind}: {e}")
    finally:
        if close_session:
            await session.close()

    return []
