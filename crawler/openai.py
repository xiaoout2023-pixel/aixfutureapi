import re
import logging
from typing import List, Dict, Any, Optional
from crawler.base import BaseCrawler, fetch_openrouter_prices

logger = logging.getLogger(__name__)

OPENAI_MODELS_META = {
    "gpt-5.5": {"model_name": "GPT-5.5", "context_length": 1000000, "reasoning_level": "high",
                "features": {"vision": True, "tool_calling": True, "audio": False, "code_generation": True},
                "release_date": "2026-04-23"},
    "gpt-5.4": {"model_name": "GPT-5.4", "context_length": 1050000, "reasoning_level": "high",
                "features": {"vision": True, "tool_calling": True, "audio": False, "code_generation": True},
                "release_date": "2026-03-05"},
    "gpt-5.4-mini": {"model_name": "GPT-5.4 Mini", "context_length": 400000, "reasoning_level": "medium",
                     "features": {"vision": True, "tool_calling": True, "audio": False, "code_generation": True},
                     "release_date": "2026-03-05"},
    "gpt-5.4-nano": {"model_name": "GPT-5.4 Nano", "context_length": 400000, "reasoning_level": "low",
                     "features": {"vision": True, "tool_calling": True, "audio": False, "code_generation": True},
                     "release_date": "2026-03-05"},
    "o3": {"model_name": "O3", "context_length": 200000, "reasoning_level": "high",
           "features": {"vision": True, "tool_calling": True, "audio": False, "code_generation": True},
           "release_date": "2025-01-20"},
    "o3-mini": {"model_name": "O3 Mini", "context_length": 200000, "reasoning_level": "high",
                "features": {"vision": False, "tool_calling": True, "audio": False, "code_generation": True},
                "release_date": "2025-01-31"},
    "gpt-4o": {"model_name": "GPT-4o", "context_length": 128000, "reasoning_level": "high",
               "features": {"vision": True, "tool_calling": True, "audio": True, "code_generation": True},
               "release_date": "2024-05-13"},
    "gpt-4o-mini": {"model_name": "GPT-4o Mini", "context_length": 128000, "reasoning_level": "medium",
                    "features": {"vision": True, "tool_calling": True, "audio": False, "code_generation": True},
                    "release_date": "2024-07-18"},
}

OPENROUTER_ID_MAP = {
    "gpt-5.5": "openai/gpt-5.5",
    "gpt-5.4": "openai/gpt-5.4",
    "gpt-5.4-mini": "openai/gpt-5.4-mini",
    "gpt-5.4-nano": "openai/gpt-5.4-nano",
    "o3": "openai/o3",
    "o3-mini": "openai/o4-mini",
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o-mini": "openai/gpt-4o-mini",
}

FALLBACK_PRICES = {
    "gpt-5.5": {"input": 5.00, "cached_input": 0.50, "output": 30.00},
    "gpt-5.4": {"input": 2.50, "cached_input": 0.25, "output": 15.00},
    "gpt-5.4-mini": {"input": 0.75, "cached_input": 0.075, "output": 4.50},
    "gpt-5.4-nano": {"input": 0.20, "cached_input": 0.02, "output": 1.25},
    "o3": {"input": 2.00, "cached_input": 0.50, "output": 8.00},
    "o3-mini": {"input": 1.10, "cached_input": 0.275, "output": 4.40},
    "gpt-4o": {"input": 2.50, "cached_input": 1.25, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "cached_input": 0.075, "output": 0.60},
}


class OpenAICrawler(BaseCrawler):
    def __init__(self):
        super().__init__(
            provider="openai",
            base_url="https://platform.openai.com/docs/models"
        )
        self.source_url = "https://platform.openai.com/docs/pricing"

    async def crawl(self) -> List[Dict[str, Any]]:
        logger.info("Starting OpenAI crawler...")

        live_prices = {}
        or_prices = await fetch_openrouter_prices()
        for model_id, or_id in OPENROUTER_ID_MAP.items():
            if or_id in or_prices:
                live_prices[model_id] = or_prices[or_id]
                logger.info(f"  Got {model_id} price from OpenRouter: {live_prices[model_id]}")

        if not live_prices:
            logger.warning("OpenRouter prices unavailable, using fallback prices")

        models = []
        for model_id, meta in OPENAI_MODELS_META.items():
            price = live_prices.get(model_id) or FALLBACK_PRICES.get(model_id, {})
            input_price = price.get("input", 0)
            output_price = price.get("output", 0)

            source = "live" if model_id in live_prices else "fallback"
            logger.info(f"  {meta['model_name']}: input=${input_price}, output=${output_price} [{source}]")

            model_record = self.create_model_record(
                model_id=model_id,
                model_name=meta["model_name"],
                context_length=meta["context_length"],
                input_price=input_price,
                output_price=output_price,
                features=meta["features"],
                source_url=self.source_url,
                release_date=meta["release_date"],
                status="active",
                reasoning_level=meta["reasoning_level"],
            )
            models.append(model_record)

        logger.info(f"OpenAI crawler completed, found {len(models)} models")
        return models
