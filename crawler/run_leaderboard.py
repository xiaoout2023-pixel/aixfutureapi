import asyncio
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.superclue import SuperCLUECrawler
from db.turso import TursoDB
from db.repository import ModelRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_leaderboard_crawl():
    logger.info("=" * 50)
    logger.info("Starting SuperCLUE leaderboard crawl...")
    logger.info(f"APP_ENV: {os.environ.get('APP_ENV', 'dev')}")
    logger.info("=" * 50)

    crawler = SuperCLUECrawler()
    entries = []
    errors = []

    try:
        entries = await crawler.crawl()
        logger.info(f"Total entries collected: {len(entries)}")
    except Exception as e:
        logger.error(f"Error crawling SuperCLUE: {e}")
        errors.append(str(e))

    if entries:
        try:
            db = TursoDB()
            repo = ModelRepository(db)
            logger.info(f"Database URL: {db.url}")

            batch_size = 50
            for i in range(0, len(entries), batch_size):
                batch = entries[i:i + batch_size]
                await repo.save_leaderboard_entries(batch)
                logger.info(f"Saved batch {i // batch_size + 1}/{(len(entries) + batch_size - 1) // batch_size}")

            logger.info(f"Saved total {len(entries)} leaderboard entries")
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            errors.append(str(e))

    categories = set(e["category"] for e in entries)
    logger.info(f"Categories covered: {len(categories)}")
    for cat in sorted(categories):
        count = sum(1 for e in entries if e["category"] == cat)
        logger.info(f"  {cat}: {count} entries")

    if errors:
        logger.warning(f"Encountered {len(errors)} errors:")
        for err in errors:
            logger.warning(f"  - {err}")

    logger.info("=" * 50)
    logger.info("Leaderboard crawl completed!")
    logger.info("=" * 50)

    return entries, errors


if __name__ == "__main__":
    asyncio.run(run_leaderboard_crawl())
