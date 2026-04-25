import httpx
from typing import List, Dict, Any
from datetime import datetime
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

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
