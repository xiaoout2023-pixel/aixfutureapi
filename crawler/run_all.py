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
from crawler.openrouter import OpenRouterCrawler
from crawler.google_gemini import GeminiCrawler
from crawler.mistral import MistralCrawler
from crawler.baidu import BaiduCrawler
from crawler.zhipu import ZhipuCrawler
from crawler.domestic import DeepSeekCrawler, MoonshotCrawler, MiniMaxCrawler
from db.turso import TursoDB
from db.repository import ModelRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def run_all_crawlers():
    logger.info("=" * 50)
    logger.info("Starting all model crawlers...")
    logger.info("=" * 50)

    crawlers = [
        ("OpenAI", OpenAICrawler()),
        ("Anthropic", AnthropicCrawler()),
        ("Aliyun", AliyunCrawler()),
        ("Google Gemini", GeminiCrawler()),
        ("Mistral", MistralCrawler()),
        ("Baidu", BaiduCrawler()),
        ("Zhipu", ZhipuCrawler()),
        ("DeepSeek", DeepSeekCrawler()),
        ("Moonshot", MoonshotCrawler()),
        ("MiniMax", MiniMaxCrawler()),
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

    logger.info(f"Total models from official crawlers: {len(all_models)}")

    try:
        logger.info("Running OpenRouter crawler (marketplace)...")
        or_crawler = OpenRouterCrawler()
        or_models = await or_crawler.crawl()
        logger.info(f"OpenRouter: {len(or_models)} models")

        existing_ids = {m["model_id"] for m in all_models}
        new_models = [m for m in or_models if m["model_id"] not in existing_ids]
        logger.info(f"OpenRouter new models (not in official): {len(new_models)}")
        all_models.extend(new_models)

        marketplace_entries = await or_crawler.crawl_marketplace_data()
        logger.info(f"OpenRouter marketplace entries: {len(marketplace_entries)}")
    except Exception as e:
        error_msg = f"Error crawling OpenRouter: {e}"
        logger.error(error_msg)
        errors.append(error_msg)
        marketplace_entries = []

    logger.info(f"Total models to save: {len(all_models)}")

    try:
        db = TursoDB()
        repo = ModelRepository(db)

        batch_size = 50
        for i in range(0, len(all_models), batch_size):
            batch = all_models[i:i + batch_size]
            await repo.save_models(batch)
            logger.info(f"Saved batch {i // batch_size + 1}/{(len(all_models) + batch_size - 1) // batch_size} ({len(batch)} models)")
        logger.info(f"Saved total {len(all_models)} models to Turso database")

        if marketplace_entries:
            for i in range(0, len(marketplace_entries), batch_size):
                batch = marketplace_entries[i:i + batch_size]
                await repo.save_marketplace_entries(batch)
                logger.info(f"Saved marketplace batch {i // batch_size + 1}")
            logger.info(f"Saved total {len(marketplace_entries)} marketplace entries")
    except Exception as e:
        error_msg = f"Error saving to Turso: {e}"
        logger.error(error_msg)
        errors.append(error_msg)

    if errors:
        logger.warning(f"Encountered {len(errors)} errors:")
        for err in errors:
            logger.warning(f"  - {err}")

    logger.info("=" * 50)
    logger.info("All crawlers completed!")
    logger.info("=" * 50)

    return all_models, errors


if __name__ == "__main__":
    asyncio.run(run_all_crawlers())
