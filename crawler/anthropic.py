import re
import logging
from typing import List, Dict, Any, Optional
from crawler.base import BaseCrawler

logger = logging.getLogger(__name__)

ANTHROPIC_MODELS_META = {
    "claude-opus-4-7": {"model_name": "Claude Opus 4.7", "context_length": 1000000, "reasoning_level": "high",
                        "features": {"vision": True, "tool_calling": True, "audio": False, "code_generation": True},
                        "release_date": "2026-04-15", "status": "active"},
    "claude-opus-4-6": {"model_name": "Claude Opus 4.6", "context_length": 1000000, "reasoning_level": "high",
                        "features": {"vision": True, "tool_calling": True, "audio": False, "code_generation": True},
                        "release_date": "2026-03-01", "status": "active"},
    "claude-opus-4-5": {"model_name": "Claude Opus 4.5", "context_length": 200000, "reasoning_level": "high",
                        "features": {"vision": True, "tool_calling": True, "audio": False, "code_generation": True},
                        "release_date": "2026-01-15", "status": "active"},
    "claude-sonnet-4-6": {"model_name": "Claude Sonnet 4.6", "context_length": 1000000, "reasoning_level": "high",
                          "features": {"vision": True, "tool_calling": True, "audio": False, "code_generation": True},
                          "release_date": "2026-03-01", "status": "active"},
    "claude-sonnet-4-5": {"model_name": "Claude Sonnet 4.5", "context_length": 200000, "reasoning_level": "high",
                          "features": {"vision": True, "tool_calling": True, "audio": False, "code_generation": True},
                          "release_date": "2026-01-15", "status": "active"},
    "claude-sonnet-4-20250514": {"model_name": "Claude Sonnet 4", "context_length": 200000, "reasoning_level": "high",
                                 "features": {"vision": True, "tool_calling": True, "audio": False, "code_generation": True},
                                 "release_date": "2025-05-14", "status": "active"},
    "claude-haiku-4-5": {"model_name": "Claude Haiku 4.5", "context_length": 200000, "reasoning_level": "medium",
                         "features": {"vision": True, "tool_calling": True, "audio": False, "code_generation": True},
                         "release_date": "2025-10-01", "status": "active"},
    "claude-3-5-haiku": {"model_name": "Claude 3.5 Haiku", "context_length": 200000, "reasoning_level": "medium",
                         "features": {"vision": True, "tool_calling": True, "audio": False, "code_generation": True},
                         "release_date": "2024-11-05", "status": "active"},
    "claude-3-opus": {"model_name": "Claude 3 Opus", "context_length": 200000, "reasoning_level": "high",
                      "features": {"vision": True, "tool_calling": True, "audio": False, "code_generation": True},
                      "release_date": "2024-03-04", "status": "deprecated"},
}

FALLBACK_PRICES = {
    "claude-opus-4-7": {"input": 5.00, "cached_input": 0.50, "output": 25.00},
    "claude-opus-4-6": {"input": 5.00, "cached_input": 0.50, "output": 25.00},
    "claude-opus-4-5": {"input": 5.00, "cached_input": 0.50, "output": 25.00},
    "claude-sonnet-4-6": {"input": 3.00, "cached_input": 0.30, "output": 15.00},
    "claude-sonnet-4-5": {"input": 3.00, "cached_input": 0.30, "output": 15.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "cached_input": 0.30, "output": 15.00},
    "claude-haiku-4-5": {"input": 1.00, "cached_input": 0.10, "output": 5.00},
    "claude-3-5-haiku": {"input": 0.80, "cached_input": 0.08, "output": 4.00},
    "claude-3-opus": {"input": 15.00, "cached_input": 1.50, "output": 75.00},
}


def _extract_pricing_from_page(html: str) -> Dict[str, Dict[str, Any]]:
    prices = {}
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)

    model_names = [
        (r'Claude\s+Opus\s+4\.7', "claude-opus-4-7"),
        (r'Claude\s+Opus\s+4\.6', "claude-opus-4-6"),
        (r'Claude\s+Opus\s+4\.5', "claude-opus-4-5"),
        (r'Claude\s+Opus\s+4\.1', "claude-opus-4-1"),
        (r'Claude\s+Opus\s+4[^.0-9]', "claude-opus-4"),
        (r'Claude\s+Sonnet\s+4\.6', "claude-sonnet-4-6"),
        (r'Claude\s+Sonnet\s+4\.5', "claude-sonnet-4-5"),
        (r'Claude\s+Sonnet\s+4[^.0-9]', "claude-sonnet-4-20250514"),
        (r'Claude\s+Haiku\s+4\.5', "claude-haiku-4-5"),
        (r'Claude\s+Haiku\s+3\.5', "claude-3-5-haiku"),
    ]

    for pattern, model_id in model_names:
        match = re.search(pattern + r'(.*?)(?:Claude\s|$)', text, re.IGNORECASE)
        if not match:
            continue
        section = match.group(1)[:300]
        all_prices = re.findall(r'\$([\d.]+)', section)
        if len(all_prices) >= 2:
            prices[model_id] = {
                "input": float(all_prices[0]),
                "output": float(all_prices[-1]),
            }
            logger.info(f"  Parsed {model_id}: input=${prices[model_id]['input']}, output=${prices[model_id]['output']}")

    return prices


class AnthropicCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(
            provider="anthropic",
            base_url="https://docs.anthropic.com/en/docs/models-overview"
        )
        self.source_url = "https://docs.anthropic.com/zh-CN/docs/about-claude/pricing"

    async def crawl(self) -> List[Dict[str, Any]]:
        logger.info("Starting Anthropic crawler...")

        live_prices = {}
        try:
            html = await self.fetch_page(self.source_url)
            live_prices = _extract_pricing_from_page(html)
            logger.info(f"Extracted live prices for {len(live_prices)} models from Anthropic pricing page")
        except Exception as e:
            logger.warning(f"Failed to fetch Anthropic pricing page: {e}, using fallback prices")

        models = []
        for model_id, meta in ANTHROPIC_MODELS_META.items():
            price = live_prices.get(model_id) or FALLBACK_PRICES.get(model_id, {})
            input_price = price.get("input", 0)
            output_price = price.get("output", 0)
            cached_input = price.get("cached_input")

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
                status=meta.get("status", "active"),
                reasoning_level=meta["reasoning_level"],
            )
            models.append(model_record)

        logger.info(f"Anthropic crawler completed, found {len(models)} models")
        return models
