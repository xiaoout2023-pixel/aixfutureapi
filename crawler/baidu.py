import json
import logging
import time
from typing import List, Dict, Any
from crawler.base import BaseCrawler

logger = logging.getLogger(__name__)

CNY_TO_USD = 7.25

BAIDU_MODELS_META = {
    "ernie-4.0-8k": {"model_name": "ERNIE 4.0", "context_length": 8000,
                     "reasoning_level": "high", "vision": False, "code": True, "reasoning": True, "tool_use": True},
    "ernie-4.0-turbo-8k": {"model_name": "ERNIE 4.0 Turbo", "context_length": 8000,
                           "reasoning_level": "medium", "vision": False, "code": True, "reasoning": False, "tool_use": True},
    "ernie-3.5-8k": {"model_name": "ERNIE 3.5", "context_length": 8000,
                     "reasoning_level": "low", "vision": False, "code": False, "reasoning": False, "tool_use": False},
    "ernie-speed-128k": {"model_name": "ERNIE Speed", "context_length": 128000,
                         "reasoning_level": "low", "vision": False, "code": False, "reasoning": False, "tool_use": True},
    "ernie-lite-8k": {"model_name": "ERNIE Lite", "context_length": 8000,
                      "reasoning_level": "low", "vision": False, "code": False, "reasoning": False, "tool_use": False},
    "ernie-vil": {"model_name": "ERNIE VL", "context_length": 8000,
                  "reasoning_level": "medium", "vision": True, "code": False, "reasoning": False, "tool_use": False},
}

BAIDU_PRICES_CNY = {
    "ernie-4.0-8k": {"input": 0.12, "output": 0.12},
    "ernie-4.0-turbo-8k": {"input": 0.03, "output": 0.06},
    "ernie-3.5-8k": {"input": 0.004, "output": 0.008},
    "ernie-speed-128k": {"input": 0.004, "output": 0.008},
    "ernie-lite-8k": {"input": 0.003, "output": 0.006},
    "ernie-vil": {"input": 0.02, "output": 0.04},
}


def _cny_to_usd_per_1m(cny_per_1k):
    return round(cny_per_1k / CNY_TO_USD * 1000, 6)


class BaiduCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="baidu", base_url="https://cloud.baidu.com")

    async def crawl(self) -> List[Dict[str, Any]]:
        logger.info("Starting Baidu crawler...")
        models = []
        for model_id, meta in BAIDU_MODELS_META.items():
            cny = BAIDU_PRICES_CNY.get(model_id, {})
            input_usd = _cny_to_usd_per_1m(cny.get("input", 0))
            output_usd = _cny_to_usd_per_1m(cny.get("output", 0))
            capabilities = {
                "text": True, "vision": meta["vision"], "audio": False, "code": meta["code"],
                "reasoning": meta["reasoning"], "tool_use": meta["tool_use"], "function_calling": meta["tool_use"],
                "image_generation": False, "video_understanding": False, "video_generation": False,
                "json_mode": True, "structured_output": False, "code_execution": False,
                "fine_tuning": True, "embedding": False,
                "context_length": meta["context_length"], "max_output_tokens": 4096,
                "reasoning_level": meta["reasoning_level"],
            }
            pricing = {
                "input_per_1m_tokens": input_usd, "output_per_1m_tokens": output_usd,
                "cached_input_price": None, "batch_input_price": None, "batch_output_price": None,
                "price_per_image": None, "price_per_request": None, "reasoning_price_per_1m": None,
                "currency": "USD", "free_tier": False,
            }
            scores = self._calc_scores(meta["reasoning_level"], input_usd, output_usd, meta["code"])
            tags = self.generate_tags(capabilities, pricing)
            source = {
                "model_page": "https://cloud.baidu.com/doc/WENXINWORKSHOP/index.html",
                "api_docs": "https://cloud.baidu.com/doc/WENXINWORKSHOP/s/flfmc9do2",
                "pricing_page": "https://cloud.baidu.com/doc/WENXINWORKSHOP/s/blhmv2k3g",
                "last_updated": time.strftime("%Y-%m-%d"), "source_type": "official",
                "region_restriction": True, "enterprise_only": False,
                "openai_compatible": False, "sdk_support": True,
            }
            models.append({
                "model_id": model_id, "model_name": meta["model_name"], "provider": "baidu",
                "release_date": None, "status": "active",
                "capabilities": json.dumps(capabilities, ensure_ascii=False),
                "pricing": json.dumps(pricing, ensure_ascii=False),
                "scores": json.dumps(scores, ensure_ascii=False),
                "tags": json.dumps(tags, ensure_ascii=False),
                "source": json.dumps(source, ensure_ascii=False),
                "last_updated": time.strftime("%Y-%m-%d"),
            })
        logger.info(f"Baidu crawler completed, found {len(models)} models")
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
