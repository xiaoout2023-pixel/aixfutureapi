import json
import logging
import time
from typing import List, Dict, Any
from crawler.base import BaseCrawler, fetch_openrouter_prices

logger = logging.getLogger(__name__)

MISTRAL_MODELS_META = {
    "mistral-large-latest": {"model_name": "Mistral Large 3", "context_length": 128000,
                             "reasoning_level": "high", "vision": False, "code": True,
                             "reasoning": True, "tool_use": True, "structured_output": True},
    "mistral-medium-latest": {"model_name": "Mistral Medium", "context_length": 128000,
                              "reasoning_level": "medium", "vision": False, "code": True,
                              "reasoning": False, "tool_use": True, "structured_output": True},
    "mistral-small-latest": {"model_name": "Mistral Small", "context_length": 128000,
                             "reasoning_level": "low", "vision": False, "code": False,
                             "reasoning": False, "tool_use": True, "structured_output": True},
    "codestral-latest": {"model_name": "Codestral", "context_length": 256000,
                         "reasoning_level": "high", "vision": False, "code": True,
                         "reasoning": False, "tool_use": False, "structured_output": True},
    "pixtral-large-latest": {"model_name": "Pixtral Large", "context_length": 128000,
                             "reasoning_level": "high", "vision": True, "code": True,
                             "reasoning": True, "tool_use": True, "structured_output": True},
    "mistral-embed": {"model_name": "Mistral Embed", "context_length": 32000,
                      "reasoning_level": "low", "vision": False, "code": False,
                      "reasoning": False, "tool_use": False, "structured_output": False},
}

OPENROUTER_ID_MAP = {
    "mistral-large-latest": "mistralai/mistral-large-latest",
    "mistral-medium-latest": "mistralai/mistral-medium-latest",
    "mistral-small-latest": "mistralai/mistral-small-latest",
    "codestral-latest": "mistralai/codestral-latest",
    "pixtral-large-latest": "mistralai/pixtral-large-latest",
    "mistral-embed": "mistralai/mistral-embed",
}

FALLBACK_PRICES = {
    "mistral-large-latest": {"input": 2.00, "output": 6.00},
    "mistral-medium-latest": {"input": 0.40, "output": 2.00},
    "mistral-small-latest": {"input": 0.20, "output": 0.60},
    "codestral-latest": {"input": 0.30, "output": 0.90},
    "pixtral-large-latest": {"input": 2.00, "output": 6.00},
    "mistral-embed": {"input": 0.10, "output": 0.10},
}


class MistralCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="mistral", base_url="https://mistral.ai")

    async def crawl(self) -> List[Dict[str, Any]]:
        logger.info("Starting Mistral crawler...")

        live_prices = {}
        or_prices = await fetch_openrouter_prices()
        for model_id, or_id in OPENROUTER_ID_MAP.items():
            if or_id in or_prices:
                live_prices[model_id] = or_prices[or_id]

        if not live_prices:
            logger.warning("OpenRouter prices unavailable, using fallback prices")

        models = []
        for model_id, meta in MISTRAL_MODELS_META.items():
            price = live_prices.get(model_id) or FALLBACK_PRICES.get(model_id, {})
            input_price = price.get("input", 0)
            output_price = price.get("output", 0)

            source = "live" if model_id in live_prices else "fallback"
            logger.info(f"  {meta['model_name']}: input=${input_price}, output=${output_price} [{source}]")

            is_embedding = "embed" in model_id
            capabilities = {
                "text": True, "vision": meta["vision"], "audio": False, "code": meta["code"],
                "reasoning": meta["reasoning"], "tool_use": meta["tool_use"], "function_calling": meta["tool_use"],
                "image_generation": False, "video_understanding": False, "video_generation": False,
                "json_mode": meta["structured_output"], "structured_output": meta["structured_output"],
                "code_execution": False, "fine_tuning": True, "embedding": is_embedding,
                "context_length": meta["context_length"], "max_output_tokens": 8192,
                "reasoning_level": meta["reasoning_level"],
            }
            pricing = {
                "input_per_1m_tokens": input_price, "output_per_1m_tokens": output_price,
                "cached_input_price": None, "batch_input_price": None, "batch_output_price": None,
                "price_per_image": None, "price_per_request": None, "reasoning_price_per_1m": None,
                "currency": "USD", "free_tier": False,
            }
            scores = self._calc_scores(meta["reasoning_level"], input_price, output_price, meta["code"])
            tags = self.generate_tags(capabilities, pricing)
            source_data = {
                "model_page": "https://docs.mistral.ai/getting-started/models/models_overview/",
                "api_docs": "https://docs.mistral.ai/api/",
                "pricing_page": "https://mistral.ai/pricing/",
                "last_updated": time.strftime("%Y-%m-%d"), "source_type": "official",
                "region_restriction": False, "enterprise_only": False,
                "openai_compatible": True, "sdk_support": True,
            }
            models.append({
                "model_id": model_id, "model_name": meta["model_name"], "provider": "mistral",
                "release_date": None, "status": "active",
                "capabilities": json.dumps(capabilities, ensure_ascii=False),
                "pricing": json.dumps(pricing, ensure_ascii=False),
                "scores": json.dumps(scores, ensure_ascii=False),
                "tags": json.dumps(tags, ensure_ascii=False),
                "source": json.dumps(source_data, ensure_ascii=False),
                "last_updated": time.strftime("%Y-%m-%d"),
            })
        logger.info(f"Mistral crawler completed, found {len(models)} models")
        return models

    def _calc_scores(self, reasoning_level, input_price, output_price, has_code):
        speed_score = 75
        reasoning_score = {"high": 90, "medium": 70, "low": 50}[reasoning_level]
        coding_score = reasoning_score - 5 if has_code else reasoning_score - 15
        cost_efficiency = max(0, 100 - (input_price + output_price) * 2)
        overall = round(reasoning_score * 0.3 + coding_score * 0.2 + speed_score * 0.2 + cost_efficiency * 0.3, 1)
        return {
            "reasoning_score": reasoning_score, "coding_score": coding_score,
            "speed_score": speed_score, "cost_efficiency_score": round(cost_efficiency, 1),
            "overall_score": overall, "latency_level": "medium", "throughput_level": "high",
        }
