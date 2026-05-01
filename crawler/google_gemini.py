import json
import logging
import time
from typing import List, Dict, Any
from crawler.base import BaseCrawler, fetch_openrouter_prices

logger = logging.getLogger(__name__)

GEMINI_MODELS_META = {
    "gemini-3.1-pro-preview": {"model_name": "Gemini 3.1 Pro", "context_length": 1048576, "max_output_tokens": 65536,
                               "reasoning_level": "high", "vision": True, "audio": True, "code": True,
                               "reasoning": True, "tool_use": True, "structured_output": True},
    "gemini-3.1-flash-preview": {"model_name": "Gemini 3.1 Flash", "context_length": 1048576, "max_output_tokens": 65536,
                                 "reasoning_level": "high", "vision": True, "audio": True, "code": True,
                                 "reasoning": True, "tool_use": True, "structured_output": True},
    "gemini-2.5-pro": {"model_name": "Gemini 2.5 Pro", "context_length": 1048576, "max_output_tokens": 65536,
                       "reasoning_level": "high", "vision": True, "audio": True, "code": True,
                       "reasoning": True, "tool_use": True, "structured_output": True},
    "gemini-2.5-flash": {"model_name": "Gemini 2.5 Flash", "context_length": 1048576, "max_output_tokens": 65536,
                         "reasoning_level": "high", "vision": True, "audio": True, "code": True,
                         "reasoning": True, "tool_use": True, "structured_output": True},
    "gemini-2.0-flash": {"model_name": "Gemini 2.0 Flash", "context_length": 1048576, "max_output_tokens": 8192,
                         "reasoning_level": "medium", "vision": True, "audio": True, "code": True,
                         "reasoning": False, "tool_use": True, "structured_output": True},
    "gemini-2.0-flash-lite": {"model_name": "Gemini 2.0 Flash Lite", "context_length": 1048576, "max_output_tokens": 8192,
                              "reasoning_level": "low", "vision": True, "audio": False, "code": False,
                              "reasoning": False, "tool_use": True, "structured_output": False},
}

OPENROUTER_ID_MAP = {
    "gemini-3.1-pro-preview": "google/gemini-3.1-pro-preview",
    "gemini-3.1-flash-preview": "google/gemini-3.1-flash-preview",
    "gemini-2.5-pro": "google/gemini-2.5-pro-preview",
    "gemini-2.5-flash": "google/gemini-2.5-flash-preview",
    "gemini-2.0-flash": "google/gemini-2.0-flash-001",
    "gemini-2.0-flash-lite": "google/gemini-2.0-flash-lite-001",
}

FALLBACK_PRICES = {
    "gemini-3.1-pro-preview": {"input": 2.00, "output": 12.00},
    "gemini-3.1-flash-preview": {"input": 0.50, "output": 3.00},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.0-flash-lite": {"input": 0.075, "output": 0.30},
}


class GeminiCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="google", base_url="https://ai.google.dev")

    async def crawl(self) -> List[Dict[str, Any]]:
        logger.info("Starting Gemini crawler...")

        live_prices = {}
        or_prices = await fetch_openrouter_prices()
        for model_id, or_id in OPENROUTER_ID_MAP.items():
            if or_id in or_prices:
                live_prices[model_id] = or_prices[or_id]

        if not live_prices:
            logger.warning("OpenRouter prices unavailable, using fallback prices")

        models = []
        for model_id, meta in GEMINI_MODELS_META.items():
            price = live_prices.get(model_id) or FALLBACK_PRICES.get(model_id, {})
            input_price = price.get("input", 0)
            output_price = price.get("output", 0)
            cached_input = price.get("cached_input")

            source = "live" if model_id in live_prices else "fallback"
            logger.info(f"  {meta['model_name']}: input=${input_price}, output=${output_price} [{source}]")

            capabilities = {
                "text": True, "vision": meta["vision"], "audio": meta["audio"], "code": meta["code"],
                "reasoning": meta["reasoning"], "tool_use": meta["tool_use"], "function_calling": meta["tool_use"],
                "image_generation": False, "video_understanding": meta["vision"], "video_generation": False,
                "json_mode": meta["structured_output"], "structured_output": meta["structured_output"],
                "code_execution": True, "fine_tuning": False, "embedding": False,
                "context_length": meta["context_length"], "max_output_tokens": meta["max_output_tokens"],
                "reasoning_level": meta["reasoning_level"],
            }
            pricing = {
                "input_per_1m_tokens": input_price, "output_per_1m_tokens": output_price,
                "cached_input_price": cached_input, "batch_input_price": None,
                "batch_output_price": None, "price_per_image": None, "price_per_request": None,
                "reasoning_price_per_1m": None, "currency": "USD", "free_tier": False,
            }
            scores = self._calc_scores(meta["reasoning_level"], input_price, output_price, meta["code"])
            tags = self.generate_tags(capabilities, pricing)
            source_data = {
                "model_page": "https://ai.google.dev/gemini-api/docs/models",
                "api_docs": "https://ai.google.dev/api",
                "pricing_page": "https://ai.google.dev/pricing",
                "last_updated": time.strftime("%Y-%m-%d"), "source_type": "official",
                "region_restriction": False, "enterprise_only": False,
                "openai_compatible": False, "sdk_support": True,
            }
            models.append({
                "model_id": model_id, "model_name": meta["model_name"], "provider": "google",
                "release_date": None, "status": "active",
                "capabilities": json.dumps(capabilities, ensure_ascii=False),
                "pricing": json.dumps(pricing, ensure_ascii=False),
                "scores": json.dumps(scores, ensure_ascii=False),
                "tags": json.dumps(tags, ensure_ascii=False),
                "source": json.dumps(source_data, ensure_ascii=False),
                "last_updated": time.strftime("%Y-%m-%d"),
            })
        logger.info(f"Gemini crawler completed, found {len(models)} models")
        return models

    def _calc_scores(self, reasoning_level, input_price, output_price, has_code):
        speed_score = 80
        reasoning_score = {"high": 90, "medium": 70, "low": 50}[reasoning_level]
        coding_score = reasoning_score - 5 if has_code else reasoning_score - 15
        cost_efficiency = max(0, 100 - (input_price + output_price) * 2)
        overall = round(reasoning_score * 0.3 + coding_score * 0.2 + speed_score * 0.2 + cost_efficiency * 0.3, 1)
        return {
            "reasoning_score": reasoning_score, "coding_score": coding_score,
            "speed_score": speed_score, "cost_efficiency_score": round(cost_efficiency, 1),
            "overall_score": overall, "latency_level": "low", "throughput_level": "high",
        }
