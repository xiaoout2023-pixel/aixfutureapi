import asyncio
import json
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.openai import OpenAICrawler
from crawler.anthropic import AnthropicCrawler
from crawler.aliyun import AliyunCrawler
from db.turso import TursoDB
from db.repository import ModelRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

async def run_all_crawlers():
    logger.info("="*50)
    logger.info("Starting all model crawlers...")
    logger.info("="*50)

    crawlers = [
        ("OpenAI", OpenAICrawler()),
        ("Anthropic", AnthropicCrawler()),
        ("Aliyun", AliyunCrawler())
    ]

    all_models = []
    errors = []

    for name, crawler in crawlers:
        try:
            logger.info(f"Running {name} crawler...")
            models = await crawler.crawl()
            all_models.extend(models)
            logger.info(f"{name} crawler completed: {len(models)} models")
        except Exception as e:
            error_msg = f"Error crawling {name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    logger.info(f"Total models collected: {len(all_models)}")

    try:
        db = TursoDB()
        repo = ModelRepository(db)
        await repo.save_models(all_models)
        logger.info(f"Saved {len(all_models)} models to Turso database")
    except Exception as e:
        error_msg = f"Error saving to Turso: {e}"
        logger.error(error_msg)
        errors.append(error_msg)

    if errors:
        logger.warning(f"Encountered {len(errors)} errors:")
        for err in errors:
            logger.warning(f"  - {err}")

    logger.info("="*50)
    logger.info("All crawlers completed!")
    logger.info("="*50)

    return all_models, errors

if __name__ == "__main__":
    asyncio.run(run_all_crawlers())
