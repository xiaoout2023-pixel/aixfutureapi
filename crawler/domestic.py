import json
import logging
import time
from typing import List, Dict, Any
from crawler.base import BaseCrawler, fetch_openrouter_prices

logger = logging.getLogger(__name__)

DEEPSEEK_MODELS_META = {
    "deepseek-chat": {"model_name": "DeepSeek V3", "context_length": 65536,
                      "reasoning_level": "high", "vision": False, "code": True, "reasoning": False, "tool_use": True},
    "deepseek-reasoner": {"model_name": "DeepSeek R1", "context_length": 65536,
                          "reasoning_level": "high", "vision": False, "code": True, "reasoning": True, "tool_use": False},
}

DEEPSEEK_OR_MAP = {
    "deepseek-chat": "deepseek/deepseek-chat",
    "deepseek-reasoner": "deepseek/deepseek-reasoner",
}

DEEPSEEK_FALLBACK = {
    "deepseek-chat": {"input": 0.27, "output": 1.10, "cached_input": 0.07},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19, "cached_input": 0.14},
}

MOONSHOT_MODELS_META = {
    "moonshot-v1-auto": {"model_name": "Moonshot V1 Auto", "context_length": 128000,
                         "reasoning_level": "medium", "vision": False, "code": True, "reasoning": False, "tool_use": True},
    "moonshot-v1-8k": {"model_name": "Moonshot V1 8K", "context_length": 8192,
                       "reasoning_level": "medium", "vision": False, "code": True, "reasoning": False, "tool_use": True},
    "moonshot-v1-32k": {"model_name": "Moonshot V1 32K", "context_length": 32768,
                        "reasoning_level": "medium", "vision": False, "code": True, "reasoning": False, "tool_use": True},
}

MOONSHOT_FALLBACK = {
    "moonshot-v1-auto": {"input": 1.66, "output": 1.66},
    "moonshot-v1-8k": {"input": 1.66, "output": 1.66},
    "moonshot-v1-32k": {"input": 1.66, "output": 1.66},
}

MINIMAX_MODELS_META = {
    "minimax-text-01": {"model_name": "MiniMax Text 01", "context_length": 1048576,
                        "reasoning_level": "medium", "vision": False, "code": True, "reasoning": False, "tool_use": True},
    "minimax-vl-01": {"model_name": "MiniMax VL 01", "context_length": 1048576,
                      "reasoning_level": "medium", "vision": True, "code": True, "reasoning": False, "tool_use": True},
}

MINIMAX_FALLBACK = {
    "minimax-text-01": {"input": 0.14, "output": 0.28},
    "minimax-vl-01": {"input": 0.14, "output": 0.28},
}


def _build_model(model_id, meta, price, provider, source_info, source_type="fallback"):
    input_price = price.get("input", 0)
    output_price = price.get("output", 0)
    cached_input = price.get("cached_input")
    capabilities = {
        "text": True, "vision": meta.get("vision", False), "audio": False, "code": meta.get("code", False),
        "reasoning": meta.get("reasoning", False), "tool_use": meta.get("tool_use", False),
        "function_calling": meta.get("tool_use", False), "image_generation": False,
        "video_understanding": False, "video_generation": False,
        "json_mode": True, "structured_output": False, "code_execution": False,
        "fine_tuning": False, "embedding": False,
        "context_length": meta["context_length"], "max_output_tokens": 4096,
        "reasoning_level": meta["reasoning_level"],
    }
    pricing = {
        "input_per_1m_tokens": input_price, "output_per_1m_tokens": output_price,
        "cached_input_price": cached_input, "batch_input_price": None, "batch_output_price": None,
        "price_per_image": None, "price_per_request": None, "reasoning_price_per_1m": None,
        "currency": "USD", "free_tier": False,
    }
    speed_score = 70
    reasoning_score = {"high": 90, "medium": 70, "low": 50}[meta["reasoning_level"]]
    coding_score = reasoning_score - 5 if meta.get("code") else reasoning_score - 15
    cost_efficiency = max(0, 100 - (input_price + output_price) * 2)
    overall = round(reasoning_score * 0.3 + coding_score * 0.2 + speed_score * 0.2 + cost_efficiency * 0.3, 1)
    scores = {
        "reasoning_score": reasoning_score, "coding_score": coding_score,
        "speed_score": speed_score, "cost_efficiency_score": round(cost_efficiency, 1),
        "overall_score": overall, "latency_level": "medium", "throughput_level": "medium",
    }
    tags = []
    if capabilities["vision"]: tags.append("vision")
    if capabilities["code"]: tags.append("coding")
    if capabilities["tool_use"]: tags.append("tool_use")
    if capabilities["reasoning"]: tags.append("reasoning")
    if input_price <= 1: tags.append("cheap")
    if input_price >= 10: tags.append("premium")
    if meta["context_length"] >= 1000000: tags.append("long_context")
    source = {
        **source_info,
        "last_updated": time.strftime("%Y-%m-%d"), "source_type": "official",
        "region_restriction": True, "enterprise_only": False,
        "openai_compatible": True, "sdk_support": True,
    }
    return {
        "model_id": model_id, "model_name": meta["model_name"], "provider": provider,
        "release_date": None, "status": "active",
        "capabilities": json.dumps(capabilities, ensure_ascii=False),
        "pricing": json.dumps(pricing, ensure_ascii=False),
        "scores": json.dumps(scores, ensure_ascii=False),
        "tags": json.dumps(tags, ensure_ascii=False),
        "source": json.dumps(source, ensure_ascii=False),
        "last_updated": time.strftime("%Y-%m-%d"),
    }


class DeepSeekCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="deepseek", base_url="https://api.deepseek.com")

    async def crawl(self) -> List[Dict[str, Any]]:
        logger.info("Starting DeepSeek crawler...")
        source_info = {
            "model_page": "https://api-docs.deepseek.com/zh-cn/",
            "api_docs": "https://api-docs.deepseek.com/",
            "pricing_page": "https://api-docs.deepseek.com/zh-cn/quick_start/pricing",
        }
        live_prices = {}
        or_prices = await fetch_openrouter_prices()
        for model_id, or_id in DEEPSEEK_OR_MAP.items():
            if or_id in or_prices:
                live_prices[model_id] = or_prices[or_id]

        models = []
        for model_id, meta in DEEPSEEK_MODELS_META.items():
            price = live_prices.get(model_id) or DEEPSEEK_FALLBACK.get(model_id, {})
            source_type = "live" if model_id in live_prices else "fallback"
            logger.info(f"  {meta['model_name']}: input=${price.get('input',0)}, output=${price.get('output',0)} [{source_type}]")
            models.append(_build_model(model_id, meta, price, "deepseek", source_info, source_type))
        logger.info(f"DeepSeek crawler completed, found {len(models)} models")
        return models


class MoonshotCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="moonshot", base_url="https://api.moonshot.cn")

    async def crawl(self) -> List[Dict[str, Any]]:
        logger.info("Starting Moonshot crawler...")
        source_info = {
            "model_page": "https://platform.moonshot.cn/docs/intro",
            "api_docs": "https://platform.moonshot.cn/docs/api/chat",
            "pricing_page": "https://platform.moonshot.cn/docs/pricing/chat",
        }
        models = []
        for model_id, meta in MOONSHOT_MODELS_META.items():
            price = MOONSHOT_FALLBACK.get(model_id, {})
            models.append(_build_model(model_id, meta, price, "moonshot", source_info))
        logger.info(f"Moonshot crawler completed, found {len(models)} models")
        return models


class MiniMaxCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="minimax", base_url="https://www.minimaxi.com")

    async def crawl(self) -> List[Dict[str, Any]]:
        logger.info("Starting MiniMax crawler...")
        source_info = {
            "model_page": "https://www.minimaxi.com/document/guides/chat-model/chat",
            "api_docs": "https://www.minimaxi.com/document/guides/chat-model/chat/api",
            "pricing_page": "https://www.minimaxi.com/document/guides/chat-model/chat/price",
        }
        models = []
        for model_id, meta in MINIMAX_MODELS_META.items():
            price = MINIMAX_FALLBACK.get(model_id, {})
            models.append(_build_model(model_id, meta, price, "minimax", source_info))
        logger.info(f"MiniMax crawler completed, found {len(models)} models")
        return models
