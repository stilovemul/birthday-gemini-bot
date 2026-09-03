"""
Yandex Music API Client for Music Sommelier Module.
Provides curated continuous non-stop playlists and direct track links.
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
        "owner": "yandexmusic",
        "kind": 1635,
        "title": "Ночной драйв (Synthwave, Dark Disco & Phonk)",
        "track_count": 190,
        "url": "https://music.yandex.ru/users/yandexmusic/playlists/1635"
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

    # Fallback to My Wave (infinite streaming flow)
    return {
        "owner": "yandex",
        "kind": "radio",
        "title": "Моя Волна (Бесконечный персональный поток)",
        "track_count": 100,
        "url": "https://music.yandex.ru/radio"
    }


async def resolve_track_url(
    artist: str,
    title: str,
    session: Optional[aiohttp.ClientSession] = None
) -> str:
    """
    Finds exact direct URL to track in Yandex.Music (https://music.yandex.ru/album/{album_id}/track/{track_id}).
    """
    q = f"{artist} {title}".strip()
    enc = urllib.parse.quote(q)
    url = f"https://api.music.yandex.net/search?text={enc}&type=track&page=0"
    headers = {"Authorization": f"OAuth {YANDEX_OAUTH_TOKEN}"}

    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True

    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=3.5)) as resp:
            if resp.status == 200:
                data = await resp.json()
                tracks = data.get("result", {}).get("tracks", {}).get("results", [])
                if tracks:
                    t = tracks[0]
                    t_id = t.get("id")
                    albums = t.get("albums", [])
                    alb_id = albums[0].get("id") if albums else None
                    if alb_id:
                        return f"https://music.yandex.ru/album/{alb_id}/track/{t_id}"
                    return f"https://music.yandex.ru/track/{t_id}"
    except Exception as e:
        logger.debug(f"Track lookup error for '{q}': {e}")
    finally:
        if close_session:
            await session.close()

    return f"https://music.yandex.ru/search?text={enc}"


async def enrich_tracks_with_urls(tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enriches a list of tracks with direct Yandex.Music track URLs in parallel.
    """
    if not tracks:
        return tracks

    async with aiohttp.ClientSession() as session:
        tasks = [
            resolve_track_url(t.get("artist", ""), t.get("title", ""), session=session)
            for t in tracks
        ]
        urls = await asyncio.gather(*tasks, return_exceptions=True)

        for t, url_res in zip(tracks, urls):
            if isinstance(url_res, str):
                t["yandex_url"] = url_res
            else:
                artist = t.get("artist", "")
                title = t.get("title", "")
                enc = urllib.parse.quote(f"{artist} {title}".strip())
                t["yandex_url"] = f"https://music.yandex.ru/search?text={enc}"

    return tracks
