import asyncio
import os
import sys
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.superclue import SuperCLUELeaderboardCrawler, BASE_DIR

API_DIR = "api/data/leaderboard"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_leaderboard_crawl():
    logger.info("=" * 50)
    logger.info("Starting SuperCLUE leaderboard crawl (raw JSON mode)...")
    logger.info("=" * 50)

    crawler = SuperCLUELeaderboardCrawler()
    boards = []

    try:
        boards = await crawler.crawl_all()
        logger.info(f"Total boards collected: {len(boards)}")
    except Exception as e:
        logger.error(f"Error crawling SuperCLUE: {e}")
        return [], [str(e)]

    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(API_DIR, exist_ok=True)

    index_data = []
    for board in boards:
        key = board["key"]
        file_path = os.path.join(BASE_DIR, f"{key}.json")
        api_file_path = os.path.join(API_DIR, f"{key}.json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(board, f, ensure_ascii=False, indent=2, default=str)

        with open(api_file_path, "w", encoding="utf-8") as f:
            json.dump(board, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Saved {key}: {len(board['rows'])} entries -> {file_path}")
        logger.info(f"Saved {key}: {len(board['rows'])} entries -> {api_file_path}")

        index_data.append({
            "key": board["key"],
            "name": board["name"],
            "group": board["group"],
            "source": board.get("source", ""),
            "source_date": board.get("source_date", ""),
            "total": len(board["rows"]),
            "headers": board.get("headers", []),
            "crawl_time": board.get("crawl_time", ""),
        })

    index_path = os.path.join(BASE_DIR, "index.json")
    api_index_path = os.path.join(API_DIR, "index.json")

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    with open(api_index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    logger.info(f"\nSaved index with {len(index_data)} boards -> {index_path}")
    logger.info(f"Saved index with {len(index_data)} boards -> {api_index_path}")

    for b in index_data:
        logger.info(f"  {b['key']}: {b['name']} ({b['total']} entries, {b['source']})")

    logger.info("=" * 50)
    logger.info("Leaderboard crawl completed!")
    logger.info("=" * 50)

    return boards, []


if __name__ == "__main__":
    asyncio.run(run_leaderboard_crawl())
