import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

_or_prices_cache: Optional[Dict[str, Dict[str, Any]]] = None


async def fetch_openrouter_prices(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    global _or_prices_cache
    if _or_prices_cache is not None and not force_refresh:
        return _or_prices_cache

    prices = {}
    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            r = await client.get("https://openrouter.ai/api/v1/models",
                                 headers={"User-Agent": "AIX-Future-API-Crawler/1.0"})
            r.raise_for_status()
            data = r.json()
            for model in data.get("data", []):
                raw_id = model.get("id", "")
                pricing = model.get("pricing", {})
                prompt = float(pricing.get("prompt", "0"))
                completion = float(pricing.get("completion", "0"))
                cache_read = float(pricing.get("input_cache_read", "0"))
                if prompt > 0 or completion > 0:
                    prices[raw_id] = {
                        "input": round(prompt * 1_000_000, 6),
                        "output": round(completion * 1_000_000, 6),
                        "cached_input": round(cache_read * 1_000_000, 6) if cache_read > 0 else None,
                    }
        logger.info(f"Fetched {len(prices)} model prices from OpenRouter API")
        _or_prices_cache = prices
    except Exception as e:
        logger.warning(f"Failed to fetch OpenRouter prices: {e}")
    return prices

PROVIDER_NAME_MAPPING = {
    "anthropic": "Anthropic",
    "~anthropic": "Anthropic",
    "openai": "OpenAI",
    "~openai": "OpenAI",
    "google": "Google",
    "~google": "Google",
    "deepseek": "深度求索",
    "deepseek-ai": "深度求索",
    "bytedance": "字节跳动",
    "bytedance-seed": "字节跳动",
    "kwaipilot": "快手科技",
    "kuaishou": "快手科技",
    "moonshot": "月之暗面",
    "moonshotai": "月之暗面",
    "~moonshotai": "月之暗面",
    "zhipu": "智谱AI",
    "zhipu-ai": "智谱AI",
    "aliyun": "阿里巴巴",
    "alibaba": "阿里巴巴",
    "baidu": "百度",
    "tencent": "腾讯",
    "xiaomi": "小米",
    "minimax": "MiniMax",
    "meta": "Meta",
    "meta-llama": "Meta",
    "mistral": "Mistral AI",
    "mistralai": "Mistral AI",
    "xai": "X.AI",
    "microsoft": "Microsoft",
    "nvidia": "NVIDIA",
    "amazon": "Amazon",
    "ibm-granite": "IBM",
    "ibm": "IBM",
    "cohere": "Cohere",
    "inflection": "Inflection AI",
    "stepfun": "阶跃星辰",
    "inception": "Inception",
    "allenai": "Allen AI",
    "arcee-ai": "Arcee AI",
    "upstage": "Upstage",
    "writer": "Writer",
    "perplexity": "Perplexity",
    "rekaai": "Reka AI",
    "liquid": "Liquid AI",
    "ai21": "AI21 Labs",
    "deepmind": "Google",
    "商汤": "商汤科技",
    "sensetime": "商汤科技",
    "小米集团": "小米",
    "智谱": "智谱AI",
    "luma": "Luma AI",
    "elevenlabs": "ElevenLabs",
    "11labs": "ElevenLabs",
    "stability ai": "Stability AI",
    "stabilityai": "Stability AI",
    "black forest labs": "Black Forest Labs",
    "recraft": "Recraft",
    "pika": "Pika",
    "科大讯飞": "科大讯飞",
    "iflytek": "科大讯飞",
    "潞晨": "潞晨科技",
    "潞晨科技": "潞晨科技",
    "生数": "生数科技",
    "生数科技": "生数科技",
    "爱诗": "爱诗科技",
    "爱诗科技": "爱诗科技",
    "智象未来": "智象未来",
    "稀宇科技": "稀宇科技",
    "美团": "美团",
    "阶跃星辰": "阶跃星辰",
    "华为": "华为",
    "huawei": "华为",
    "字节跳动/火山引擎": "字节跳动",
    "火山引擎": "字节跳动",
}


def normalize_provider_name(name: str) -> str:
    if not name:
        return name
    key = name.strip().lower()
    if key in PROVIDER_NAME_MAPPING:
        return PROVIDER_NAME_MAPPING[key]
    return name.strip()


class BaseCrawler:
    def __init__(self, provider: str, base_url: str = ""):
        self.provider = provider
        self.base_url = base_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.timeout = 30
        self.max_retries = 3

    async def fetch_page(self, url: str) -> str:
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                    logger.info(f"Successfully fetched {url}")
                    return response.text
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    raise
                time.sleep(2 ** attempt)
        return ""

    def normalize_price_to_per_1m(self, price: float, unit: str) -> float:
        unit = unit.lower().strip()
        if "1m" in unit or "1,000,000" in unit:
            return price
        elif "1k" in unit or "1,000" in unit:
            return price * 1000
        elif "1 token" in unit:
            return price * 1000000
        else:
            logger.warning(f"Unknown price unit: {unit}, assuming per 1M tokens")
            return price

    def generate_tags(self, capabilities: Dict, pricing: Dict) -> List[str]:
        tags = []
        if capabilities.get("vision"):
            tags.append("vision")
        if capabilities.get("code_generation"):
            tags.append("coding")
        if capabilities.get("tool_calling"):
            tags.append("tool_use")
        if capabilities.get("multimodal"):
            tags.append("multimodal")
        if capabilities.get("reasoning_level") == "high":
            tags.append("reasoning")
        
        input_price = pricing.get("input_price_per_1m_tokens", 0)
        if input_price <= 1:
            tags.append("cheap")
        elif input_price >= 10:
            tags.append("premium")
        
        context_length = capabilities.get("context_length", 0)
        if context_length >= 1000000:
            tags.append("long_context")
        
        return tags

    def create_model_record(self, model_id: str, model_name: str, context_length: int,
                           input_price: float, output_price: float,
                           features: Dict[str, bool], model_type: str = "multimodal",
                           source_url: str = "", release_date: str = "",
                           status: str = "active", reasoning_level: str = "medium",
                           scores: Dict = None, currency: str = "USD") -> Dict[str, Any]:
        capabilities = {
            "text_generation": True,
            "code_generation": features.get("code_generation", features.get("tool_calling", True)),
            "vision": features.get("vision", False),
            "audio": features.get("audio", False),
            "multimodal": features.get("multimodal", features.get("vision", False) or features.get("audio", False)),
            "tool_calling": features.get("tool_calling", features.get("tool_use", True)),
            "context_length": context_length,
            "reasoning_level": reasoning_level
        }

        pricing = {
            "input_price_per_1m_tokens": input_price,
            "output_price_per_1m_tokens": output_price,
            "currency": currency
        }

        if not scores:
            speed_score = 75 if context_length < 200000 else 60
            reasoning_score = {"high": 90, "medium": 70, "low": 50}.get(reasoning_level, 70)
            coding_score = reasoning_score - 5
            cost_efficiency = max(0, 100 - (input_price + output_price) * 2)
            overall_score = (reasoning_score * 0.3 + coding_score * 0.2 + speed_score * 0.2 + cost_efficiency * 0.3)
            
            scores = {
                "reasoning_score": reasoning_score,
                "coding_score": coding_score,
                "speed_score": speed_score,
                "cost_efficiency_score": round(cost_efficiency, 1),
                "overall_score": round(overall_score, 1)
            }

        tags = self.generate_tags(capabilities, pricing)

        return {
            "model_id": model_id,
            "model_name": model_name,
            "provider": self.provider,
            "release_date": release_date,
            "status": status,
            "capabilities": capabilities,
            "pricing": pricing,
            "scores": scores,
            "tags": tags,
            "source": {
                "model_page": source_url,
                "api_docs": self.base_url,
                "pricing_page": source_url,
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            },
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }

    async def crawl(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("Subclasses must implement crawl()")
