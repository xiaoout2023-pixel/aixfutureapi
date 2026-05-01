import json
import logging
import time
from typing import List, Dict, Any
from crawler.base import BaseCrawler, fetch_openrouter_prices

logger = logging.getLogger(__name__)

CNY_TO_USD = 7.25

ZHIPU_MODELS_META = {
    "glm-4-plus": {"model_name": "GLM-4 Plus", "context_length": 128000,
                   "reasoning_level": "high", "vision": False, "code": True, "reasoning": True, "tool_use": True},
    "glm-4-air": {"model_name": "GLM-4 Air", "context_length": 128000,
                  "reasoning_level": "medium", "vision": False, "code": True, "reasoning": False, "tool_use": True},
    "glm-4-airx": {"model_name": "GLM-4 AirX", "context_length": 8192,
                   "reasoning_level": "medium", "vision": False, "code": False, "reasoning": False, "tool_use": False},
    "glm-4-flash": {"model_name": "GLM-4 Flash", "context_length": 128000,
                    "reasoning_level": "low", "vision": False, "code": False, "reasoning": False, "tool_use": True},
    "glm-4v-plus": {"model_name": "GLM-4V Plus", "context_length": 8192,
                    "reasoning_level": "high", "vision": True, "code": False, "reasoning": True, "tool_use": False},
    "glm-4v": {"model_name": "GLM-4V", "context_length": 2048,
               "reasoning_level": "medium", "vision": True, "code": False, "reasoning": False, "tool_use": False},
}

ZHIPU_OR_MAP = {
    "glm-4-plus": "thudm/glm-4-plus",
    "glm-4-flash": "thudm/glm-4-flash",
}

ZHIPU_PRICES_CNY = {
    "glm-4-plus": {"input": 0.05, "output": 0.05},
    "glm-4-air": {"input": 0.001, "output": 0.001},
    "glm-4-airx": {"input": 0.001, "output": 0.001},
    "glm-4-flash": {"input": 0.0001, "output": 0.0001},
    "glm-4v-plus": {"input": 0.01, "output": 0.01},
    "glm-4v": {"input": 0.01, "output": 0.01},
}


def _cny_to_usd_per_1m(cny_per_1k):
    return round(cny_per_1k / CNY_TO_USD * 1000, 6)


class ZhipuCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="zhipu", base_url="https://open.bigmodel.cn")

    async def crawl(self) -> List[Dict[str, Any]]:
        logger.info("Starting Zhipu crawler...")

        live_prices = {}
        or_prices = await fetch_openrouter_prices()
        for model_id, or_id in ZHIPU_OR_MAP.items():
            if or_id in or_prices:
                live_prices[model_id] = or_prices[or_id]

        models = []
        for model_id, meta in ZHIPU_MODELS_META.items():
            if model_id in live_prices:
                input_usd = live_prices[model_id]["input"]
                output_usd = live_prices[model_id]["output"]
                source_type = "live"
            else:
                cny = ZHIPU_PRICES_CNY.get(model_id, {})
                input_usd = _cny_to_usd_per_1m(cny.get("input", 0))
                output_usd = _cny_to_usd_per_1m(cny.get("output", 0))
                source_type = "fallback"

            logger.info(f"  {meta['model_name']}: input=${input_usd}, output=${output_usd} [{source_type}]")

            is_free = input_usd <= 0.02
            capabilities = {
                "text": True, "vision": meta["vision"], "audio": False, "code": meta["code"],
                "reasoning": meta["reasoning"], "tool_use": meta["tool_use"], "function_calling": meta["tool_use"],
                "image_generation": False, "video_understanding": False, "video_generation": False,
                "json_mode": True, "structured_output": True, "code_execution": False,
                "fine_tuning": False, "embedding": False,
                "context_length": meta["context_length"], "max_output_tokens": 4096,
                "reasoning_level": meta["reasoning_level"],
            }
            pricing = {
                "input_per_1m_tokens": input_usd, "output_per_1m_tokens": output_usd,
                "cached_input_price": None, "batch_input_price": None, "batch_output_price": None,
                "price_per_image": None, "price_per_request": None, "reasoning_price_per_1m": None,
                "currency": "USD", "free_tier": is_free,
            }
            scores = self._calc_scores(meta["reasoning_level"], input_usd, output_usd, meta["code"])
            tags = self.generate_tags(capabilities, pricing)
            source = {
                "model_page": "https://open.bigmodel.cn/dev/howuse/glm-4",
                "api_docs": "https://open.bigmodel.cn/dev/api",
                "pricing_page": "https://open.bigmodel.cn/pricing",
                "last_updated": time.strftime("%Y-%m-%d"), "source_type": "official",
                "region_restriction": True, "enterprise_only": False,
                "openai_compatible": True, "sdk_support": True,
            }
            models.append({
                "model_id": model_id, "model_name": meta["model_name"], "provider": "zhipu",
                "release_date": None, "status": "active",
                "capabilities": json.dumps(capabilities, ensure_ascii=False),
                "pricing": json.dumps(pricing, ensure_ascii=False),
                "scores": json.dumps(scores, ensure_ascii=False),
                "tags": json.dumps(tags, ensure_ascii=False),
                "source": json.dumps(source, ensure_ascii=False),
                "last_updated": time.strftime("%Y-%m-%d"),
            })
        logger.info(f"Zhipu crawler completed, found {len(models)} models")
        return models

    def _calc_scores(self, reasoning_level, input_price, output_price, has_code):
        speed_score = 70
        reasoning_score = {"high": 90, "medium": 70, "low": 50}[reasoning_level]
        coding_score = reasoning_score - 5 if has_code else reasoning_score - 15
        cost_efficiency = max(0, 100 - (input_price + output_price) * 2)
        overall = round(reasoning_score * 0.3 + coding_score * 0.2 + speed_score * 0.2 + cost_efficiency * 0.3, 1)
        return {
            "reasoning_score": reasoning_score, "coding_score": coding_score,
            "speed_score": speed_score, "cost_efficiency_score": round(cost_efficiency, 1),
            "overall_score": overall, "latency_level": "medium", "throughput_level": "medium",
        }
