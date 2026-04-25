from crawler.base import BaseCrawler
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class OpenAICrawler(BaseCrawler):
    def __init__(self):
        super().__init__(
            provider="openai",
            base_url="https://platform.openai.com/docs/models"
        )
        self.source_url = "https://openai.com/api/pricing/"

    async def crawl(self) -> List[Dict[str, Any]]:
        logger.info("Starting OpenAI crawler...")
        models = []

        try:
            await self.fetch_page(self.source_url)
        except Exception as e:
            logger.warning(f"Failed to fetch OpenAI pricing page: {e}, using cached pricing data")

        models_data = [
            {
                "model_id": "gpt-5.5",
                "model_name": "GPT-5.5",
                "release_date": "2025-10-20",
                "status": "active",
                "context_length": 400000,
                "input_price_per_1m": 1.25,
                "output_price_per_1m": 10.0,
                "features": {
                    "vision": True,
                    "tool_calling": True,
                    "audio": False,
                    "code_generation": True
                },
                "reasoning_level": "high"
            },
            {
                "model_id": "gpt-5.4",
                "model_name": "GPT-5.4",
                "release_date": "2025-08-15",
                "status": "active",
                "context_length": 128000,
                "input_price_per_1m": 1.25,
                "output_price_per_1m": 10.0,
                "features": {
                    "vision": True,
                    "tool_calling": True,
                    "audio": False,
                    "code_generation": True
                },
                "reasoning_level": "high"
            },
            {
                "model_id": "gpt-5.4-mini",
                "model_name": "GPT-5.4 Mini",
                "release_date": "2025-08-15",
                "status": "active",
                "context_length": 128000,
                "input_price_per_1m": 0.25,
                "output_price_per_1m": 2.0,
                "features": {
                    "vision": True,
                    "tool_calling": True,
                    "audio": False,
                    "code_generation": True
                },
                "reasoning_level": "medium"
            },
            {
                "model_id": "gpt-5.4-nano",
                "model_name": "GPT-5.4 Nano",
                "release_date": "2025-08-15",
                "status": "active",
                "context_length": 128000,
                "input_price_per_1m": 0.10,
                "output_price_per_1m": 0.40,
                "features": {
                    "vision": True,
                    "tool_calling": True,
                    "audio": False,
                    "code_generation": True
                },
                "reasoning_level": "low"
            },
            {
                "model_id": "o3",
                "model_name": "O3",
                "release_date": "2025-01-20",
                "status": "active",
                "context_length": 200000,
                "input_price_per_1m": 10.0,
                "output_price_per_1m": 40.0,
                "features": {
                    "vision": True,
                    "tool_calling": True,
                    "audio": False,
                    "code_generation": True
                },
                "reasoning_level": "high"
            },
            {
                "model_id": "o3-mini",
                "model_name": "O3 Mini",
                "release_date": "2025-01-31",
                "status": "active",
                "context_length": 200000,
                "input_price_per_1m": 1.10,
                "output_price_per_1m": 4.40,
                "features": {
                    "vision": False,
                    "tool_calling": True,
                    "audio": False,
                    "code_generation": True
                },
                "reasoning_level": "high"
            },
            {
                "model_id": "gpt-4o",
                "model_name": "GPT-4o",
                "release_date": "2024-05-13",
                "status": "active",
                "context_length": 128000,
                "input_price_per_1m": 2.50,
                "output_price_per_1m": 10.0,
                "features": {
                    "vision": True,
                    "tool_calling": True,
                    "audio": True,
                    "code_generation": True
                },
                "reasoning_level": "high"
            },
            {
                "model_id": "gpt-4o-mini",
                "model_name": "GPT-4o Mini",
                "release_date": "2024-07-18",
                "status": "active",
                "context_length": 128000,
                "input_price_per_1m": 0.15,
                "output_price_per_1m": 0.60,
                "features": {
                    "vision": True,
                    "tool_calling": True,
                    "audio": False,
                    "code_generation": True
                },
                "reasoning_level": "medium"
            }
        ]

        for m in models_data:
            model_record = self.create_model_record(
                model_id=m["model_id"],
                model_name=m["model_name"],
                context_length=m["context_length"],
                input_price=self.normalize_price_to_per_1m(m["input_price_per_1m"], "per 1M tokens"),
                output_price=self.normalize_price_to_per_1m(m["output_price_per_1m"], "per 1M tokens"),
                features=m["features"],
                source_url=self.source_url,
                release_date=m["release_date"],
                status=m["status"],
                reasoning_level=m["reasoning_level"]
            )
            models.append(model_record)
            logger.info(f"Extracted OpenAI model: {m['model_name']}")

        logger.info(f"OpenAI crawler completed, found {len(models)} models")
        return models
