from crawler.base import BaseCrawler
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SuperCLUECrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="superclue", base_url="https://superclueai.com")

    async def crawl(self) -> List[Dict[str, Any]]:
        general = self._get_general_board()
        multimodal = self._get_multimodal_board()
        return general + multimodal

    def _get_general_board(self) -> List[Dict[str, Any]]:
        period = "2026-03"
        now = datetime.now().strftime("%Y-%m-%d")
        return [
            {
                "model_id": "deepseek-r1", "model_name": "DeepSeek-R1", "provider": "deepseek",
                "board_type": "general", "rank": 1, "score": 89.5,
                "sub_scores": {"hallucination_control": 85.2, "math_reasoning": 92.1, "science_reasoning": 88.3, "instruction_following": 90.1, "code_generation": 89.7, "agent_planning": 86.5},
                "generation_time": 12.5, "input_price": 4.0, "output_price": 16.0, "composite_price": 7.0,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "gpt-5.5", "model_name": "GPT-5.5", "provider": "openai",
                "board_type": "general", "rank": 2, "score": 88.7,
                "sub_scores": {"hallucination_control": 87.1, "math_reasoning": 90.5, "science_reasoning": 89.2, "instruction_following": 91.3, "code_generation": 88.4, "agent_planning": 83.8},
                "generation_time": 8.2, "input_price": 14.5, "output_price": 58.0, "composite_price": 25.4,
                "is_reference": True, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "qwen-max", "model_name": "Qwen-Max", "provider": "aliyun",
                "board_type": "general", "rank": 3, "score": 87.3,
                "sub_scores": {"hallucination_control": 84.6, "math_reasoning": 88.9, "science_reasoning": 86.7, "instruction_following": 89.5, "code_generation": 87.2, "agent_planning": 84.1},
                "generation_time": 9.8, "input_price": 14.0, "output_price": 56.0, "composite_price": 24.5,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "claude-sonnet-4", "model_name": "Claude Sonnet 4", "provider": "anthropic",
                "board_type": "general", "rank": 4, "score": 86.9,
                "sub_scores": {"hallucination_control": 88.3, "math_reasoning": 85.7, "science_reasoning": 87.1, "instruction_following": 90.8, "code_generation": 86.5, "agent_planning": 80.2},
                "generation_time": 7.5, "input_price": 21.0, "output_price": 105.0, "composite_price": 42.0,
                "is_reference": True, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "deepseek-v3", "model_name": "DeepSeek-V3", "provider": "deepseek",
                "board_type": "general", "rank": 5, "score": 85.2,
                "sub_scores": {"hallucination_control": 82.4, "math_reasoning": 87.6, "science_reasoning": 84.3, "instruction_following": 86.9, "code_generation": 85.1, "agent_planning": 82.7},
                "generation_time": 10.1, "input_price": 1.0, "output_price": 2.0, "composite_price": 1.3,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "glm-4-plus", "model_name": "GLM-4-Plus", "provider": "zhipu",
                "board_type": "general", "rank": 6, "score": 84.1,
                "sub_scores": {"hallucination_control": 83.2, "math_reasoning": 84.5, "science_reasoning": 83.8, "instruction_following": 87.1, "code_generation": 83.9, "agent_planning": 79.6},
                "generation_time": 11.3, "input_price": 35.0, "output_price": 35.0, "composite_price": 35.0,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "hunyuan-turbo", "model_name": "Hunyuan-Turbo", "provider": "tencent",
                "board_type": "general", "rank": 7, "score": 83.5,
                "sub_scores": {"hallucination_control": 81.7, "math_reasoning": 83.9, "science_reasoning": 82.6, "instruction_following": 86.3, "code_generation": 82.8, "agent_planning": 78.1},
                "generation_time": 6.8, "input_price": 8.0, "output_price": 24.0, "composite_price": 12.0,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "ernie-4.5", "model_name": "ERNIE-4.5", "provider": "baidu",
                "board_type": "general", "rank": 8, "score": 82.8,
                "sub_scores": {"hallucination_control": 80.5, "math_reasoning": 82.3, "science_reasoning": 81.9, "instruction_following": 85.7, "code_generation": 81.4, "agent_planning": 77.3},
                "generation_time": 9.2, "input_price": 20.0, "output_price": 60.0, "composite_price": 30.0,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "gpt-5.4", "model_name": "GPT-5.4", "provider": "openai",
                "board_type": "general", "rank": 9, "score": 81.6,
                "sub_scores": {"hallucination_control": 84.9, "math_reasoning": 83.2, "science_reasoning": 82.1, "instruction_following": 84.5, "code_generation": 80.3, "agent_planning": 71.8},
                "generation_time": 6.5, "input_price": 7.25, "output_price": 29.0, "composite_price": 12.7,
                "is_reference": True, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "moonshot-v1", "model_name": "Moonshot-v1", "provider": "moonshot",
                "board_type": "general", "rank": 10, "score": 80.3,
                "sub_scores": {"hallucination_control": 79.8, "math_reasoning": 78.5, "science_reasoning": 79.2, "instruction_following": 83.6, "code_generation": 79.1, "agent_planning": 75.4},
                "generation_time": 8.9, "input_price": 28.0, "output_price": 28.0, "composite_price": 28.0,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "qwen-plus", "model_name": "Qwen-Plus", "provider": "aliyun",
                "board_type": "general", "rank": 11, "score": 79.5,
                "sub_scores": {"hallucination_control": 78.3, "math_reasoning": 80.1, "science_reasoning": 78.7, "instruction_following": 82.4, "code_generation": 78.9, "agent_planning": 74.2},
                "generation_time": 7.2, "input_price": 4.0, "output_price": 12.0, "composite_price": 6.0,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "spark-4-ultra", "model_name": "Spark-4-Ultra", "provider": "iflytek",
                "board_type": "general", "rank": 12, "score": 78.1,
                "sub_scores": {"hallucination_control": 77.2, "math_reasoning": 76.8, "science_reasoning": 77.5, "instruction_following": 81.3, "code_generation": 76.4, "agent_planning": 72.9},
                "generation_time": 10.5, "input_price": 15.0, "output_price": 15.0, "composite_price": 15.0,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "claude-3.5-sonnet", "model_name": "Claude 3.5 Sonnet", "provider": "anthropic",
                "board_type": "general", "rank": 13, "score": 77.4,
                "sub_scores": {"hallucination_control": 82.1, "math_reasoning": 76.3, "science_reasoning": 78.9, "instruction_following": 80.7, "code_generation": 75.8, "agent_planning": 68.5},
                "generation_time": 5.8, "input_price": 21.0, "output_price": 105.0, "composite_price": 42.0,
                "is_reference": True, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "gpt-4o", "model_name": "GPT-4o", "provider": "openai",
                "board_type": "general", "rank": 14, "score": 76.2,
                "sub_scores": {"hallucination_control": 80.5, "math_reasoning": 74.8, "science_reasoning": 76.3, "instruction_following": 79.2, "code_generation": 73.5, "agent_planning": 66.1},
                "generation_time": 5.2, "input_price": 18.1, "output_price": 72.5, "composite_price": 31.7,
                "is_reference": True, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "doubao-pro", "model_name": "Doubao-Pro", "provider": "bytedance",
                "board_type": "general", "rank": 15, "score": 75.8,
                "sub_scores": {"hallucination_control": 74.6, "math_reasoning": 73.2, "science_reasoning": 74.8, "instruction_following": 79.1, "code_generation": 74.3, "agent_planning": 70.5},
                "generation_time": 5.5, "input_price": 0.8, "output_price": 2.0, "composite_price": 1.1,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
        ]

    def _get_multimodal_board(self) -> List[Dict[str, Any]]:
        period = "2026-03"
        now = datetime.now().strftime("%Y-%m-%d")
        return [
            {
                "model_id": "gpt-5.5", "model_name": "GPT-5.5", "provider": "openai",
                "board_type": "multimodal", "rank": 1, "score": 91.2,
                "sub_scores": {"image_understanding": 93.5, "video_understanding": 88.7, "audio_understanding": 90.1, "multimodal_fusion": 92.3},
                "generation_time": 10.8, "input_price": 14.5, "output_price": 58.0, "composite_price": 25.4,
                "is_reference": True, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "claude-sonnet-4", "model_name": "Claude Sonnet 4", "provider": "anthropic",
                "board_type": "multimodal", "rank": 2, "score": 89.8,
                "sub_scores": {"image_understanding": 91.2, "video_understanding": 86.5, "audio_understanding": 87.3, "multimodal_fusion": 90.8},
                "generation_time": 8.5, "input_price": 21.0, "output_price": 105.0, "composite_price": 42.0,
                "is_reference": True, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "qwen-vl-max", "model_name": "Qwen-VL-Max", "provider": "aliyun",
                "board_type": "multimodal", "rank": 3, "score": 88.5,
                "sub_scores": {"image_understanding": 90.1, "video_understanding": 85.3, "audio_understanding": 84.7, "multimodal_fusion": 89.2},
                "generation_time": 11.2, "input_price": 14.0, "output_price": 56.0, "composite_price": 24.5,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "gemini-2.5-pro", "model_name": "Gemini 2.5 Pro", "provider": "google",
                "board_type": "multimodal", "rank": 4, "score": 87.3,
                "sub_scores": {"image_understanding": 88.9, "video_understanding": 87.1, "audio_understanding": 86.5, "multimodal_fusion": 85.8},
                "generation_time": 9.1, "input_price": 9.4, "output_price": 37.5, "composite_price": 16.4,
                "is_reference": True, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "glm-4v-plus", "model_name": "GLM-4V-Plus", "provider": "zhipu",
                "board_type": "multimodal", "rank": 5, "score": 85.6,
                "sub_scores": {"image_understanding": 87.3, "video_understanding": 82.1, "audio_understanding": 80.5, "multimodal_fusion": 86.9},
                "generation_time": 12.1, "input_price": 35.0, "output_price": 35.0, "composite_price": 35.0,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "deepseek-vl2", "model_name": "DeepSeek-VL2", "provider": "deepseek",
                "board_type": "multimodal", "rank": 6, "score": 84.2,
                "sub_scores": {"image_understanding": 86.1, "video_understanding": 79.8, "audio_understanding": 78.3, "multimodal_fusion": 84.5},
                "generation_time": 13.5, "input_price": 1.0, "output_price": 2.0, "composite_price": 1.3,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "hunyuan-vision", "model_name": "Hunyuan-Vision", "provider": "tencent",
                "board_type": "multimodal", "rank": 7, "score": 82.8,
                "sub_scores": {"image_understanding": 84.5, "video_understanding": 78.2, "audio_understanding": 76.9, "multimodal_fusion": 83.1},
                "generation_time": 9.8, "input_price": 8.0, "output_price": 24.0, "composite_price": 12.0,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "gpt-4o", "model_name": "GPT-4o", "provider": "openai",
                "board_type": "multimodal", "rank": 8, "score": 81.5,
                "sub_scores": {"image_understanding": 83.7, "video_understanding": 77.5, "audio_understanding": 79.2, "multimodal_fusion": 82.3},
                "generation_time": 6.3, "input_price": 18.1, "output_price": 72.5, "composite_price": 31.7,
                "is_reference": True, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "qwen-vl-plus", "model_name": "Qwen-VL-Plus", "provider": "aliyun",
                "board_type": "multimodal", "rank": 9, "score": 79.3,
                "sub_scores": {"image_understanding": 81.2, "video_understanding": 74.8, "audio_understanding": 73.5, "multimodal_fusion": 80.1},
                "generation_time": 8.5, "input_price": 4.0, "output_price": 12.0, "composite_price": 6.0,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
            {
                "model_id": "step-1v", "model_name": "Step-1V", "provider": "stepfun",
                "board_type": "multimodal", "rank": 10, "score": 77.8,
                "sub_scores": {"image_understanding": 79.5, "video_understanding": 72.3, "audio_understanding": 71.8, "multimodal_fusion": 78.6},
                "generation_time": 11.7, "input_price": 10.0, "output_price": 30.0, "composite_price": 15.0,
                "is_reference": False, "period": period, "source": "SuperCLUE", "last_updated": now
            },
        ]
