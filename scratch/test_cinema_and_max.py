import sys
import os
import asyncio
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, r"c:\Users\olegu\BirthdayReminder\render_cloud")

from core.fsm_storage import JsonFsmStorage
from aiogram.fsm.storage.base import StorageKey
from modules.cinema_matchmaker.storage import (
    get_user_cinema_memory,
    mark_all_last_recommended_as_watched,
    clean_title_str
)
from modules.cinema_matchmaker.recommender import detect_query_intent, recommend_movies
from modules.max_tracker.checker import ext_to_hex


async def run_all_tests():
    print("--- 1. Testing JsonFsmStorage ---")
    storage = JsonFsmStorage()
    key = StorageKey(bot_id=12345, chat_id=157236577, user_id=157236577)
    await storage.set_state(key, "ActiveModeStates:cinema_matchmaker_mode")
    st = await storage.get_state(key)
    assert st == "ActiveModeStates:cinema_matchmaker_mode", f"Expected state saved, got: {st}"
    print(f"JsonFsmStorage state: {st} - OK")

    print("\n--- 2. Testing MAX deduplication and ext_to_hex ---")
    h1 = ext_to_hex("d301a0573683e132d6")
    assert h1 == "d301a0573683e132d6"
    assert ext_to_hex(None) == ""
    print("MAX ext_to_hex - OK")

    print("\n--- 3. Testing Cinema user phrase: 'Всё, смотрели, понравился только лада голд' ---")
    test_user_id = 999999999
    q1 = "Всё, смотрели, понравился только лада голд"
    intent = detect_query_intent(q1, {"format": "сериал", "country": "Россия"})
    print(f"Detected intent for '{q1}': {intent}")
    assert intent["is_watched_all"] is True or intent["is_more"] is True

    res = await recommend_movies(test_user_id, q1)
    print("Recommended movies:")
    for idx, m in enumerate(res.get("movies", []), 1):
        print(f"  {idx}. {m.get('title_ru')} ({m.get('title_orig')})")
    assert len(res.get("movies", [])) == 5

    print("\n--- 4. Testing Cinema user phrase: 'Уже посмотрели, советуй еще что-нибудь и желательно 2025-2026 годов' ---")
    q2 = "Уже посмотрели, советуй еще что-нибудь и желательно 2025-2026 годов"
    res2 = await recommend_movies(test_user_id, q2)
    print("Recommended fresh movies:")
    for idx, m in enumerate(res2.get("movies", []), 1):
        print(f"  {idx}. {m.get('title_ru')} ({m.get('title_orig')})")
    assert len(res2.get("movies", [])) == 5

    print("\n✅ All comprehensive tests passed successfully!")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
