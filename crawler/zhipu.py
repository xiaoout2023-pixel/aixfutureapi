import json
import logging
import time
from typing import List, Dict, Any
from crawler.base import BaseCrawler

logger = logging.getLogger(__name__)

CNY_TO_USD = 7.25

ZHIPU_MODELS = [
    {"model_id": "glm-4-plus", "model_name": "GLM-4 Plus", "context_length": 128000,
     "input_price_cny": 0.05, "output_price_cny": 0.05, "reasoning_level": "high",
     "vision": False, "code": True, "reasoning": True, "tool_use": True},
    {"model_id": "glm-4-air", "model_name": "GLM-4 Air", "context_length": 128000,
     "input_price_cny": 0.001, "output_price_cny": 0.001, "reasoning_level": "medium",
     "vision": False, "code": True, "reasoning": False, "tool_use": True},
    {"model_id": "glm-4-airx", "model_name": "GLM-4 AirX", "context_length": 8192,
     "input_price_cny": 0.001, "output_price_cny": 0.001, "reasoning_level": "medium",
     "vision": False, "code": False, "reasoning": False, "tool_use": False},
    {"model_id": "glm-4-flash", "model_name": "GLM-4 Flash", "context_length": 128000,
     "input_price_cny": 0.0001, "output_price_cny": 0.0001, "reasoning_level": "low",
     "vision": False, "code": False, "reasoning": False, "tool_use": True},
    {"model_id": "glm-4v-plus", "model_name": "GLM-4V Plus", "context_length": 8192,
     "input_price_cny": 0.01, "output_price_cny": 0.01, "reasoning_level": "high",
     "vision": True, "code": False, "reasoning": True, "tool_use": False},
    {"model_id": "glm-4v", "model_name": "GLM-4V", "context_length": 2048,
     "input_price_cny": 0.01, "output_price_cny": 0.01, "reasoning_level": "medium",
     "vision": True, "code": False, "reasoning": False, "tool_use": False},
]


class ZhipuCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="zhipu", base_url="https://open.bigmodel.cn")

    async def crawl(self) -> List[Dict[str, Any]]:
        models = []
        for m in ZHIPU_MODELS:
            input_usd = round(m["input_price_cny"] / CNY_TO_USD * 1000, 6)
            output_usd = round(m["output_price_cny"] / CNY_TO_USD * 1000, 6)
            capabilities = {
                "text": True, "vision": m["vision"], "audio": False, "code": m["code"],
                "reasoning": m["reasoning"], "tool_use": m["tool_use"], "function_calling": m["tool_use"],
                "image_generation": False, "video_understanding": False, "video_generation": False,
                "json_mode": True, "structured_output": True, "code_execution": False,
                "fine_tuning": False, "embedding": False,
                "context_length": m["context_length"], "max_output_tokens": 4096,
                "reasoning_level": m["reasoning_level"],
            }
            pricing = {
                "input_per_1m_tokens": input_usd, "output_per_1m_tokens": output_usd,
                "cached_input_price": None, "batch_input_price": None, "batch_output_price": None,
                "price_per_image": None, "price_per_request": None, "reasoning_price_per_1m": None,
                "currency": "USD", "free_tier": m["input_price_cny"] <= 0.0001,
            }
            scores = self._calc_scores(m["reasoning_level"], input_usd, output_usd, m["code"])
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
                "model_id": m["model_id"], "model_name": m["model_name"], "provider": "zhipu",
                "release_date": None, "status": "active",
                "capabilities": json.dumps(capabilities, ensure_ascii=False),
                "pricing": json.dumps(pricing, ensure_ascii=False),
                "scores": json.dumps(scores, ensure_ascii=False),
                "tags": json.dumps(tags, ensure_ascii=False),
                "source": json.dumps(source, ensure_ascii=False),
                "last_updated": time.strftime("%Y-%m-%d"),
            })
        logger.info(f"Collected {len(models)} Zhipu models")
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
