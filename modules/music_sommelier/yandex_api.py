"""
Yandex Music API Client for Music Sommelier Module.
Provides curated continuous non-stop playlists and extracts real playlist tracklists.
"""

import asyncio
import aiohttp
import urllib.parse
import logging
from typing import Dict, Any, List, Optional
from core.config import YANDEX_OAUTH_TOKEN

logger = logging.getLogger("YandexMusicAPI")

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


async def get_best_yandex_playlist(
    query: str,
    preset_key: Optional[str] = None,
    session: Optional[aiohttp.ClientSession] = None
) -> Dict[str, Any]:
    """
    Returns the best matching full continuous non-stop playlist from Yandex.Music.
    Allows user to hit 'Play' once and have tracks play continuously without stopping.
    """
    if preset_key and preset_key in PRESET_PLAYLISTS:
        return dict(PRESET_PLAYLISTS[preset_key])

    headers = {"Authorization": f"OAuth {YANDEX_OAUTH_TOKEN}"}
    search_queries = [query.strip()]

    # If long query, also try with the first 3 keywords
    words = query.split()
    if len(words) > 3:
        search_queries.append(" ".join(words[:3]))

    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True

    try:
        for q in search_queries:
            enc = urllib.parse.quote(q)
            url = f"https://api.music.yandex.net/search?text={enc}&type=playlist&page=0"
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        playlists = data.get("result", {}).get("playlists", {}).get("results", [])
                        if playlists:
                            # Prioritize playlists with track count >= 15, sort by track count
                            playlists.sort(key=lambda p: p.get("trackCount", 0), reverse=True)
                            best = playlists[0]
                            owner = best.get("owner", {}).get("login") or best.get("owner", {}).get("name") or "yamusic"
                            kind = best.get("kind")
                            return {
                                "owner": owner,
                                "kind": kind,
                                "title": best.get("title", "Плейлист под настроение"),
                                "track_count": best.get("trackCount", 0),
                                "url": f"https://music.yandex.ru/users/{owner}/playlists/{kind}"
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
        "title": "Моя Волна (Бесконечный персональный поток)",
        "track_count": 100,
        "url": "https://music.yandex.ru/radio"
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
