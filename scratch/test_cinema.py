import sys
import os
import asyncio

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, r"c:\Users\olegu\BirthdayReminder\render_cloud")

from modules.cinema_matchmaker.storage import (
    get_user_cinema_memory,
    add_or_update_movie_feedback,
    mark_all_last_recommended_as_watched,
    get_all_excluded_titles,
    get_active_search_context,
    set_active_search_context,
    append_dialog_turn,
    get_dialog_history,
    set_last_recommended_movies,
    clean_title_str
)
from modules.cinema_matchmaker.catalog import get_curated_fallback, RUSSIAN_SERIES
from modules.cinema_matchmaker.recommender import detect_query_intent, recommend_movies


async def test_cinema():
    print("--- 1. Testing clean_title_str ---")
    t1 = clean_title_str("«ЮЗЗЗ» (2022)")
    assert t1 == "ЮЗЗЗ", f"Got: {t1}"
    print(f"Clean title: '{t1}' - OK")

    print("\n--- 2. Testing detect_query_intent ---")
    q1 = "хочу русский сериал, мы сейчас смотрим ЮЗЗЗ, очень нравится, еще смотрели Капельник и тоже понравился. Хочу что-то подобное"
    intent1 = detect_query_intent(q1, {})
    print(f"Intent 1: {intent1}")
    assert intent1["format"] == "сериал", f"Expected format 'сериал', got {intent1['format']}"
    assert intent1["country"] == "Россия", f"Expected country 'Россия', got {intent1['country']}"

    q2 = "всё смотрел, давай другое что-нибудь"
    intent2 = detect_query_intent(q2, {"format": "сериал", "country": "Россия"})
    print(f"Intent 2: {intent2}")
    assert intent2["is_watched_all"] is True, "Expected is_watched_all True"
    assert intent2["is_more"] is True, "Expected is_more True"
    assert intent2["format"] == "сериал", "Should retain format"
    assert intent2["country"] == "Россия", "Should retain country"

    print("\n--- 3. Testing Fallback Database Filtering ---")
    excluded = ["ЮЗЗЗ", "Капельник", "Мир! Дружба! Жвачка!", "Чики", "Король и Шут"]
    fb = get_curated_fallback(format_type="сериал", country="Россия", excluded_titles=excluded)
    print(f"Fallback 5 series: {[x['title_ru'] for x in fb]}")
    assert len(fb) == 5, f"Expected 5, got {len(fb)}"
    for item in fb:
        assert item["title_ru"] not in excluded, f"Item {item['title_ru']} should not be in excluded!"
    print("Fallback filtering - OK")

    print("\n--- 4. Testing End-to-End Recommendation Flow ---")
    test_user_id = 999999999
    # Step 1: User asks for Russian series
    res1 = await recommend_movies(test_user_id, q1)
    print("Step 1 Results:")
    print(f"  Thought: {res1.get('thought_process')[:80]}...")
    print(f"  Movies: {[m.get('title_ru') for m in res1.get('movies', [])]}")
    m_titles_1 = [clean_title_str(m.get('title_ru')) for m in res1.get('movies', [])]

    # Step 2: User says "всё смотрел, давай другое"
    res2 = await recommend_movies(test_user_id, q2)
    print("\nStep 2 Results (after 'всё смотрел'):")
    print(f"  Thought: {res2.get('thought_process')[:80]}...")
    print(f"  Movies: {[m.get('title_ru') for m in res2.get('movies', [])]}")
    m_titles_2 = [clean_title_str(m.get('title_ru')) for m in res2.get('movies', [])]

    # Check that Step 2 didn't repeat Step 1
    for t in m_titles_2:
        assert t not in m_titles_1, f"Duplicate found across batches: {t} was in Step 1!"
    print("\nAnti-loop verification passed! No repeated titles across batches.")

    print("\n✅ All cinema tests passed successfully!")


if __name__ == "__main__":
    asyncio.run(test_cinema())
