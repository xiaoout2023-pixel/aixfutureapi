from crawler.base import BaseCrawler
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

PERIOD = "2026-03"

OVERALL_MODELS = [
    {"model_id": "deepseek-r1", "model_name": "DeepSeek-R1", "provider": "deepseek", "is_reference": False, "score": 89.5, "generation_time": 12.5, "input_price": 4.0, "output_price": 16.0, "composite_price": 7.0},
    {"model_id": "gpt-5.5", "model_name": "GPT-5.5", "provider": "openai", "is_reference": True, "score": 88.7, "generation_time": 8.2, "input_price": 14.5, "output_price": 58.0, "composite_price": 25.4},
    {"model_id": "qwen-max", "model_name": "Qwen-Max", "provider": "aliyun", "is_reference": False, "score": 87.3, "generation_time": 9.8, "input_price": 14.0, "output_price": 56.0, "composite_price": 24.5},
    {"model_id": "claude-sonnet-4", "model_name": "Claude Sonnet 4", "provider": "anthropic", "is_reference": True, "score": 86.9, "generation_time": 7.5, "input_price": 21.0, "output_price": 105.0, "composite_price": 42.0},
    {"model_id": "deepseek-v3", "model_name": "DeepSeek-V3", "provider": "deepseek", "is_reference": False, "score": 85.2, "generation_time": 10.1, "input_price": 1.0, "output_price": 2.0, "composite_price": 1.3},
    {"model_id": "glm-4-plus", "model_name": "GLM-4-Plus", "provider": "zhipu", "is_reference": False, "score": 84.1, "generation_time": 11.3, "input_price": 35.0, "output_price": 35.0, "composite_price": 35.0},
    {"model_id": "hunyuan-turbo", "model_name": "Hunyuan-Turbo", "provider": "tencent", "is_reference": False, "score": 83.5, "generation_time": 6.8, "input_price": 8.0, "output_price": 24.0, "composite_price": 12.0},
    {"model_id": "ernie-4.5", "model_name": "ERNIE-4.5", "provider": "baidu", "is_reference": False, "score": 82.8, "generation_time": 9.2, "input_price": 20.0, "output_price": 60.0, "composite_price": 30.0},
    {"model_id": "gpt-5.4", "model_name": "GPT-5.4", "provider": "openai", "is_reference": True, "score": 81.6, "generation_time": 6.5, "input_price": 7.25, "output_price": 29.0, "composite_price": 12.7},
    {"model_id": "moonshot-v1", "model_name": "Moonshot-v1", "provider": "moonshot", "is_reference": False, "score": 80.3, "generation_time": 8.9, "input_price": 28.0, "output_price": 28.0, "composite_price": 28.0},
    {"model_id": "qwen-plus", "model_name": "Qwen-Plus", "provider": "aliyun", "is_reference": False, "score": 79.5, "generation_time": 7.2, "input_price": 4.0, "output_price": 12.0, "composite_price": 6.0},
    {"model_id": "spark-4-ultra", "model_name": "Spark-4-Ultra", "provider": "iflytek", "is_reference": False, "score": 78.1, "generation_time": 10.5, "input_price": 15.0, "output_price": 15.0, "composite_price": 15.0},
    {"model_id": "claude-3.5-sonnet", "model_name": "Claude 3.5 Sonnet", "provider": "anthropic", "is_reference": True, "score": 77.4, "generation_time": 5.8, "input_price": 21.0, "output_price": 105.0, "composite_price": 42.0},
    {"model_id": "gpt-4o", "model_name": "GPT-4o", "provider": "openai", "is_reference": True, "score": 76.2, "generation_time": 5.2, "input_price": 18.1, "output_price": 72.5, "composite_price": 31.7},
    {"model_id": "doubao-pro", "model_name": "Doubao-Pro", "provider": "bytedance", "is_reference": False, "score": 75.8, "generation_time": 5.5, "input_price": 0.8, "output_price": 2.0, "composite_price": 1.1},
]

REASONING_MODELS = [
    {"model_id": "deepseek-r1", "model_name": "DeepSeek-R1", "provider": "deepseek", "is_reference": False, "score": 92.3, "generation_time": 18.5, "input_price": 4.0, "output_price": 16.0, "composite_price": 7.0},
    {"model_id": "gpt-5.5", "model_name": "GPT-5.5", "provider": "openai", "is_reference": True, "score": 91.1, "generation_time": 12.3, "input_price": 14.5, "output_price": 58.0, "composite_price": 25.4},
    {"model_id": "claude-sonnet-4", "model_name": "Claude Sonnet 4", "provider": "anthropic", "is_reference": True, "score": 89.7, "generation_time": 10.8, "input_price": 21.0, "output_price": 105.0, "composite_price": 42.0},
    {"model_id": "qwen-max", "model_name": "Qwen-Max", "provider": "aliyun", "is_reference": False, "score": 88.4, "generation_time": 14.2, "input_price": 14.0, "output_price": 56.0, "composite_price": 24.5},
    {"model_id": "deepseek-v3", "model_name": "DeepSeek-V3", "provider": "deepseek", "is_reference": False, "score": 86.5, "generation_time": 15.1, "input_price": 1.0, "output_price": 2.0, "composite_price": 1.3},
    {"model_id": "glm-4-plus", "model_name": "GLM-4-Plus", "provider": "zhipu", "is_reference": False, "score": 84.2, "generation_time": 16.3, "input_price": 35.0, "output_price": 35.0, "composite_price": 35.0},
    {"model_id": "hunyuan-turbo", "model_name": "Hunyuan-Turbo", "provider": "tencent", "is_reference": False, "score": 82.8, "generation_time": 9.5, "input_price": 8.0, "output_price": 24.0, "composite_price": 12.0},
    {"model_id": "ernie-4.5", "model_name": "ERNIE-4.5", "provider": "baidu", "is_reference": False, "score": 81.5, "generation_time": 13.1, "input_price": 20.0, "output_price": 60.0, "composite_price": 30.0},
    {"model_id": "gpt-5.4", "model_name": "GPT-5.4", "provider": "openai", "is_reference": True, "score": 80.3, "generation_time": 9.2, "input_price": 7.25, "output_price": 29.0, "composite_price": 12.7},
    {"model_id": "spark-4-ultra", "model_name": "Spark-4-Ultra", "provider": "iflytek", "is_reference": False, "score": 78.6, "generation_time": 14.8, "input_price": 15.0, "output_price": 15.0, "composite_price": 15.0},
]

BASE_MODELS = [
    {"model_id": "gpt-5.5", "model_name": "GPT-5.5", "provider": "openai", "is_reference": True, "score": 88.2, "generation_time": 6.8, "input_price": 14.5, "output_price": 58.0, "composite_price": 25.4},
    {"model_id": "qwen-max", "model_name": "Qwen-Max", "provider": "aliyun", "is_reference": False, "score": 86.9, "generation_time": 8.1, "input_price": 14.0, "output_price": 56.0, "composite_price": 24.5},
    {"model_id": "claude-sonnet-4", "model_name": "Claude Sonnet 4", "provider": "anthropic", "is_reference": True, "score": 85.7, "generation_time": 5.9, "input_price": 21.0, "output_price": 105.0, "composite_price": 42.0},
    {"model_id": "deepseek-v3", "model_name": "DeepSeek-V3", "provider": "deepseek", "is_reference": False, "score": 84.3, "generation_time": 8.5, "input_price": 1.0, "output_price": 2.0, "composite_price": 1.3},
    {"model_id": "glm-4-plus", "model_name": "GLM-4-Plus", "provider": "zhipu", "is_reference": False, "score": 83.5, "generation_time": 9.2, "input_price": 35.0, "output_price": 35.0, "composite_price": 35.0},
    {"model_id": "hunyuan-turbo", "model_name": "Hunyuan-Turbo", "provider": "tencent", "is_reference": False, "score": 82.1, "generation_time": 5.5, "input_price": 8.0, "output_price": 24.0, "composite_price": 12.0},
    {"model_id": "ernie-4.5", "model_name": "ERNIE-4.5", "provider": "baidu", "is_reference": False, "score": 81.4, "generation_time": 7.8, "input_price": 20.0, "output_price": 60.0, "composite_price": 30.0},
    {"model_id": "gpt-5.4", "model_name": "GPT-5.4", "provider": "openai", "is_reference": True, "score": 80.8, "generation_time": 5.1, "input_price": 7.25, "output_price": 29.0, "composite_price": 12.7},
    {"model_id": "moonshot-v1", "model_name": "Moonshot-v1", "provider": "moonshot", "is_reference": False, "score": 79.6, "generation_time": 7.3, "input_price": 28.0, "output_price": 28.0, "composite_price": 28.0},
    {"model_id": "qwen-plus", "model_name": "Qwen-Plus", "provider": "aliyun", "is_reference": False, "score": 78.2, "generation_time": 6.1, "input_price": 4.0, "output_price": 12.0, "composite_price": 6.0},
    {"model_id": "claude-3.5-sonnet", "model_name": "Claude 3.5 Sonnet", "provider": "anthropic", "is_reference": True, "score": 76.5, "generation_time": 4.5, "input_price": 21.0, "output_price": 105.0, "composite_price": 42.0},
    {"model_id": "gpt-4o", "model_name": "GPT-4o", "provider": "openai", "is_reference": True, "score": 75.3, "generation_time": 4.2, "input_price": 18.1, "output_price": 72.5, "composite_price": 31.7},
    {"model_id": "doubao-pro", "model_name": "Doubao-Pro", "provider": "bytedance", "is_reference": False, "score": 74.8, "generation_time": 4.5, "input_price": 0.8, "output_price": 2.0, "composite_price": 1.1},
]

REASONING_TASK_MODELS = [
    {"model_id": "deepseek-r1", "model_name": "DeepSeek-R1", "provider": "deepseek", "is_reference": False, "score": 93.1, "generation_time": 20.2, "input_price": 4.0, "output_price": 16.0, "composite_price": 7.0},
    {"model_id": "gpt-5.5", "model_name": "GPT-5.5", "provider": "openai", "is_reference": True, "score": 91.8, "generation_time": 13.5, "input_price": 14.5, "output_price": 58.0, "composite_price": 25.4},
    {"model_id": "claude-sonnet-4", "model_name": "Claude Sonnet 4", "provider": "anthropic", "is_reference": True, "score": 90.2, "generation_time": 11.8, "input_price": 21.0, "output_price": 105.0, "composite_price": 42.0},
    {"model_id": "qwen-max", "model_name": "Qwen-Max", "provider": "aliyun", "is_reference": False, "score": 88.9, "generation_time": 15.6, "input_price": 14.0, "output_price": 56.0, "composite_price": 24.5},
    {"model_id": "deepseek-v3", "model_name": "DeepSeek-V3", "provider": "deepseek", "is_reference": False, "score": 87.1, "generation_time": 16.3, "input_price": 1.0, "output_price": 2.0, "composite_price": 1.3},
    {"model_id": "glm-4-plus", "model_name": "GLM-4-Plus", "provider": "zhipu", "is_reference": False, "score": 85.3, "generation_time": 17.8, "input_price": 35.0, "output_price": 35.0, "composite_price": 35.0},
    {"model_id": "hunyuan-turbo", "model_name": "Hunyuan-Turbo", "provider": "tencent", "is_reference": False, "score": 83.7, "generation_time": 10.2, "input_price": 8.0, "output_price": 24.0, "composite_price": 12.0},
    {"model_id": "ernie-4.5", "model_name": "ERNIE-4.5", "provider": "baidu", "is_reference": False, "score": 82.4, "generation_time": 14.1, "input_price": 20.0, "output_price": 60.0, "composite_price": 30.0},
    {"model_id": "gpt-5.4", "model_name": "GPT-5.4", "provider": "openai", "is_reference": True, "score": 81.2, "generation_time": 10.5, "input_price": 7.25, "output_price": 29.0, "composite_price": 12.7},
    {"model_id": "spark-4-ultra", "model_name": "Spark-4-Ultra", "provider": "iflytek", "is_reference": False, "score": 79.5, "generation_time": 16.2, "input_price": 15.0, "output_price": 15.0, "composite_price": 15.0},
]

OPENSOURCE_MODELS = [
    {"model_id": "deepseek-r1", "model_name": "DeepSeek-R1", "provider": "deepseek", "is_reference": False, "score": 89.5, "generation_time": 12.5, "input_price": 4.0, "output_price": 16.0, "composite_price": 7.0},
    {"model_id": "deepseek-v3", "model_name": "DeepSeek-V3", "provider": "deepseek", "is_reference": False, "score": 85.2, "generation_time": 10.1, "input_price": 1.0, "output_price": 2.0, "composite_price": 1.3},
    {"model_id": "qwen-max", "model_name": "Qwen-Max", "provider": "aliyun", "is_reference": False, "score": 87.3, "generation_time": 9.8, "input_price": 14.0, "output_price": 56.0, "composite_price": 24.5},
    {"model_id": "glm-4-plus", "model_name": "GLM-4-Plus", "provider": "zhipu", "is_reference": False, "score": 84.1, "generation_time": 11.3, "input_price": 35.0, "output_price": 35.0, "composite_price": 35.0},
    {"model_id": "qwen-plus", "model_name": "Qwen-Plus", "provider": "aliyun", "is_reference": False, "score": 79.5, "generation_time": 7.2, "input_price": 4.0, "output_price": 12.0, "composite_price": 6.0},
    {"model_id": "llama-4-maverick", "model_name": "Llama-4-Maverick", "provider": "meta", "is_reference": True, "score": 78.8, "generation_time": 8.5, "input_price": 3.5, "output_price": 14.0, "composite_price": 6.1},
    {"model_id": "deepseek-vl2", "model_name": "DeepSeek-VL2", "provider": "deepseek", "is_reference": False, "score": 76.3, "generation_time": 13.5, "input_price": 1.0, "output_price": 2.0, "composite_price": 1.3},
    {"model_id": "qwen-vl-plus", "model_name": "Qwen-VL-Plus", "provider": "aliyun", "is_reference": False, "score": 74.5, "generation_time": 8.5, "input_price": 4.0, "output_price": 12.0, "composite_price": 6.0},
    {"model_id": "internlm3", "model_name": "InternLM3", "provider": "shanghaiai", "is_reference": False, "score": 72.1, "generation_time": 9.8, "input_price": 5.0, "output_price": 15.0, "composite_price": 7.5},
    {"model_id": "yi-lightning", "model_name": "Yi-Lightning", "provider": "01ai", "is_reference": False, "score": 70.5, "generation_time": 6.2, "input_price": 2.5, "output_price": 10.0, "composite_price": 4.4},
]

MULTIMODAL_MODELS = [
    {"model_id": "gpt-5.5", "model_name": "GPT-5.5", "provider": "openai", "is_reference": True, "score": 91.2, "generation_time": 10.8, "input_price": 14.5, "output_price": 58.0, "composite_price": 25.4},
    {"model_id": "claude-sonnet-4", "model_name": "Claude Sonnet 4", "provider": "anthropic", "is_reference": True, "score": 89.8, "generation_time": 8.5, "input_price": 21.0, "output_price": 105.0, "composite_price": 42.0},
    {"model_id": "qwen-vl-max", "model_name": "Qwen-VL-Max", "provider": "aliyun", "is_reference": False, "score": 88.5, "generation_time": 11.2, "input_price": 14.0, "output_price": 56.0, "composite_price": 24.5},
    {"model_id": "gemini-2.5-pro", "model_name": "Gemini 2.5 Pro", "provider": "google", "is_reference": True, "score": 87.3, "generation_time": 9.1, "input_price": 9.4, "output_price": 37.5, "composite_price": 16.4},
    {"model_id": "glm-4v-plus", "model_name": "GLM-4V-Plus", "provider": "zhipu", "is_reference": False, "score": 85.6, "generation_time": 12.1, "input_price": 35.0, "output_price": 35.0, "composite_price": 35.0},
    {"model_id": "deepseek-vl2", "model_name": "DeepSeek-VL2", "provider": "deepseek", "is_reference": False, "score": 84.2, "generation_time": 13.5, "input_price": 1.0, "output_price": 2.0, "composite_price": 1.3},
    {"model_id": "hunyuan-vision", "model_name": "Hunyuan-Vision", "provider": "tencent", "is_reference": False, "score": 82.8, "generation_time": 9.8, "input_price": 8.0, "output_price": 24.0, "composite_price": 12.0},
    {"model_id": "gpt-4o", "model_name": "GPT-4o", "provider": "openai", "is_reference": True, "score": 81.5, "generation_time": 6.3, "input_price": 18.1, "output_price": 72.5, "composite_price": 31.7},
    {"model_id": "qwen-vl-plus", "model_name": "Qwen-VL-Plus", "provider": "aliyun", "is_reference": False, "score": 79.3, "generation_time": 8.5, "input_price": 4.0, "output_price": 12.0, "composite_price": 6.0},
    {"model_id": "step-1v", "model_name": "Step-1V", "provider": "stepfun", "is_reference": False, "score": 77.8, "generation_time": 11.7, "input_price": 10.0, "output_price": 30.0, "composite_price": 15.0},
]

MULTIMODAL_VLM_MODELS = [
    {"model_id": "gpt-5.5", "model_name": "GPT-5.5", "provider": "openai", "is_reference": True, "score": 92.5, "generation_time": 10.8, "input_price": 14.5, "output_price": 58.0, "composite_price": 25.4},
    {"model_id": "claude-sonnet-4", "model_name": "Claude Sonnet 4", "provider": "anthropic", "is_reference": True, "score": 91.1, "generation_time": 8.5, "input_price": 21.0, "output_price": 105.0, "composite_price": 42.0},
    {"model_id": "qwen-vl-max", "model_name": "Qwen-VL-Max", "provider": "aliyun", "is_reference": False, "score": 89.8, "generation_time": 11.2, "input_price": 14.0, "output_price": 56.0, "composite_price": 24.5},
    {"model_id": "gemini-2.5-pro", "model_name": "Gemini 2.5 Pro", "provider": "google", "is_reference": True, "score": 88.2, "generation_time": 9.1, "input_price": 9.4, "output_price": 37.5, "composite_price": 16.4},
    {"model_id": "glm-4v-plus", "model_name": "GLM-4V-Plus", "provider": "zhipu", "is_reference": False, "score": 86.5, "generation_time": 12.1, "input_price": 35.0, "output_price": 35.0, "composite_price": 35.0},
    {"model_id": "deepseek-vl2", "model_name": "DeepSeek-VL2", "provider": "deepseek", "is_reference": False, "score": 85.1, "generation_time": 13.5, "input_price": 1.0, "output_price": 2.0, "composite_price": 1.3},
    {"model_id": "hunyuan-vision", "model_name": "Hunyuan-Vision", "provider": "tencent", "is_reference": False, "score": 83.7, "generation_time": 9.8, "input_price": 8.0, "output_price": 24.0, "composite_price": 12.0},
    {"model_id": "step-1v", "model_name": "Step-1V", "provider": "stepfun", "is_reference": False, "score": 78.9, "generation_time": 11.7, "input_price": 10.0, "output_price": 30.0, "composite_price": 15.0},
]

MULTIMODAL_V_MODELS = [
    {"model_id": "gpt-5.5", "model_name": "GPT-5.5", "provider": "openai", "is_reference": True, "score": 90.8, "generation_time": 10.8, "input_price": 14.5, "output_price": 58.0, "composite_price": 25.4},
    {"model_id": "claude-sonnet-4", "model_name": "Claude Sonnet 4", "provider": "anthropic", "is_reference": True, "score": 89.3, "generation_time": 8.5, "input_price": 21.0, "output_price": 105.0, "composite_price": 42.0},
    {"model_id": "qwen-vl-max", "model_name": "Qwen-VL-Max", "provider": "aliyun", "is_reference": False, "score": 87.6, "generation_time": 11.2, "input_price": 14.0, "output_price": 56.0, "composite_price": 24.5},
    {"model_id": "gemini-2.5-pro", "model_name": "Gemini 2.5 Pro", "provider": "google", "is_reference": True, "score": 86.1, "generation_time": 9.1, "input_price": 9.4, "output_price": 37.5, "composite_price": 16.4},
    {"model_id": "glm-4v-plus", "model_name": "GLM-4V-Plus", "provider": "zhipu", "is_reference": False, "score": 84.2, "generation_time": 12.1, "input_price": 35.0, "output_price": 35.0, "composite_price": 35.0},
    {"model_id": "deepseek-vl2", "model_name": "DeepSeek-VL2", "provider": "deepseek", "is_reference": False, "score": 82.8, "generation_time": 13.5, "input_price": 1.0, "output_price": 2.0, "composite_price": 1.3},
    {"model_id": "hunyuan-vision", "model_name": "Hunyuan-Vision", "provider": "tencent", "is_reference": False, "score": 81.5, "generation_time": 9.8, "input_price": 8.0, "output_price": 24.0, "composite_price": 12.0},
    {"model_id": "gpt-4o", "model_name": "GPT-4o", "provider": "openai", "is_reference": True, "score": 80.3, "generation_time": 6.3, "input_price": 18.1, "output_price": 72.5, "composite_price": 31.7},
]

MULTIMODAL_VLR_MODELS = [
    {"model_id": "deepseek-r1", "model_name": "DeepSeek-R1", "provider": "deepseek", "is_reference": False, "score": 91.2, "generation_time": 15.3, "input_price": 4.0, "output_price": 16.0, "composite_price": 7.0},
    {"model_id": "gpt-5.5", "model_name": "GPT-5.5", "provider": "openai", "is_reference": True, "score": 89.8, "generation_time": 11.5, "input_price": 14.5, "output_price": 58.0, "composite_price": 25.4},
    {"model_id": "claude-sonnet-4", "model_name": "Claude Sonnet 4", "provider": "anthropic", "is_reference": True, "score": 88.5, "generation_time": 9.8, "input_price": 21.0, "output_price": 105.0, "composite_price": 42.0},
    {"model_id": "qwen-vl-max", "model_name": "Qwen-VL-Max", "provider": "aliyun", "is_reference": False, "score": 86.3, "generation_time": 12.8, "input_price": 14.0, "output_price": 56.0, "composite_price": 24.5},
    {"model_id": "gemini-2.5-pro", "model_name": "Gemini 2.5 Pro", "provider": "google", "is_reference": True, "score": 84.7, "generation_time": 10.2, "input_price": 9.4, "output_price": 37.5, "composite_price": 16.4},
    {"model_id": "glm-4v-plus", "model_name": "GLM-4V-Plus", "provider": "zhipu", "is_reference": False, "score": 82.1, "generation_time": 13.5, "input_price": 35.0, "output_price": 35.0, "composite_price": 35.0},
]

MULTIMODAL_IMAGE_MODELS = [
    {"model_id": "dall-e-4", "model_name": "DALL-E 4", "provider": "openai", "is_reference": True, "score": 88.5, "generation_time": 12.3, "input_price": 30.0, "output_price": 30.0, "composite_price": 30.0},
    {"model_id": "midjourney-v7", "model_name": "Midjourney V7", "provider": "midjourney", "is_reference": True, "score": 90.2, "generation_time": 15.8, "input_price": 40.0, "output_price": 40.0, "composite_price": 40.0},
    {"model_id": "flux-pro", "model_name": "FLUX.1 Pro", "provider": "blackforest", "is_reference": True, "score": 87.1, "generation_time": 8.5, "input_price": 25.0, "output_price": 25.0, "composite_price": 25.0},
    {"model_id": "stable-diffusion-4", "model_name": "Stable Diffusion 4", "provider": "stability", "is_reference": True, "score": 82.3, "generation_time": 6.2, "input_price": 15.0, "output_price": 15.0, "composite_price": 15.0},
    {"model_id": "cogview-4", "model_name": "CogView-4", "provider": "zhipu", "is_reference": False, "score": 80.5, "generation_time": 10.1, "input_price": 20.0, "output_price": 20.0, "composite_price": 20.0},
]

MULTIMODAL_T2V_MODELS = [
    {"model_id": "sora", "model_name": "Sora", "provider": "openai", "is_reference": True, "score": 89.5, "generation_time": 45.2, "input_price": 50.0, "output_price": 50.0, "composite_price": 50.0},
    {"model_id": "kling-2", "model_name": "Kling 2.0", "provider": "kuaishou", "is_reference": False, "score": 85.3, "generation_time": 38.5, "input_price": 35.0, "output_price": 35.0, "composite_price": 35.0},
    {"model_id": "vidu-2", "model_name": "Vidu 2.0", "provider": "shengshu", "is_reference": False, "score": 82.1, "generation_time": 32.8, "input_price": 28.0, "output_price": 28.0, "composite_price": 28.0},
    {"model_id": "cogvideox-2", "model_name": "CogVideoX-2", "provider": "zhipu", "is_reference": False, "score": 78.6, "generation_time": 35.2, "input_price": 20.0, "output_price": 20.0, "composite_price": 20.0},
]

MULTIMODAL_I2V_MODELS = [
    {"model_id": "sora", "model_name": "Sora", "provider": "openai", "is_reference": True, "score": 88.2, "generation_time": 42.1, "input_price": 50.0, "output_price": 50.0, "composite_price": 50.0},
    {"model_id": "kling-2", "model_name": "Kling 2.0", "provider": "kuaishou", "is_reference": False, "score": 84.5, "generation_time": 36.3, "input_price": 35.0, "output_price": 35.0, "composite_price": 35.0},
    {"model_id": "vidu-2", "model_name": "Vidu 2.0", "provider": "shengshu", "is_reference": False, "score": 81.3, "generation_time": 30.5, "input_price": 28.0, "output_price": 28.0, "composite_price": 28.0},
    {"model_id": "cogvideox-2", "model_name": "CogVideoX-2", "provider": "zhipu", "is_reference": False, "score": 77.8, "generation_time": 33.1, "input_price": 20.0, "output_price": 20.0, "composite_price": 20.0},
]

MULTIMODAL_R2V_MODELS = [
    {"model_id": "sora", "model_name": "Sora", "provider": "openai", "is_reference": True, "score": 86.5, "generation_time": 48.3, "input_price": 50.0, "output_price": 50.0, "composite_price": 50.0},
    {"model_id": "kling-2", "model_name": "Kling 2.0", "provider": "kuaishou", "is_reference": False, "score": 83.2, "generation_time": 40.1, "input_price": 35.0, "output_price": 35.0, "composite_price": 35.0},
    {"model_id": "vidu-2", "model_name": "Vidu 2.0", "provider": "shengshu", "is_reference": False, "score": 79.8, "generation_time": 35.6, "input_price": 28.0, "output_price": 28.0, "composite_price": 28.0},
]

MULTIMODAL_EDIT_MODELS = [
    {"model_id": "gpt-5.5", "model_name": "GPT-5.5", "provider": "openai", "is_reference": True, "score": 87.3, "generation_time": 8.5, "input_price": 14.5, "output_price": 58.0, "composite_price": 25.4},
    {"model_id": "gemini-2.5-pro", "model_name": "Gemini 2.5 Pro", "provider": "google", "is_reference": True, "score": 85.1, "generation_time": 7.8, "input_price": 9.4, "output_price": 37.5, "composite_price": 16.4},
    {"model_id": "flux-pro", "model_name": "FLUX.1 Pro", "provider": "blackforest", "is_reference": True, "score": 83.6, "generation_time": 6.2, "input_price": 25.0, "output_price": 25.0, "composite_price": 25.0},
    {"model_id": "stable-diffusion-4", "model_name": "Stable Diffusion 4", "provider": "stability", "is_reference": True, "score": 80.2, "generation_time": 5.5, "input_price": 15.0, "output_price": 15.0, "composite_price": 15.0},
]

MULTIMODAL_COMIC_MODELS = [
    {"model_id": "dall-e-4", "model_name": "DALL-E 4", "provider": "openai", "is_reference": True, "score": 82.5, "generation_time": 18.3, "input_price": 30.0, "output_price": 30.0, "composite_price": 30.0},
    {"model_id": "midjourney-v7", "model_name": "Midjourney V7", "provider": "midjourney", "is_reference": True, "score": 85.1, "generation_time": 22.5, "input_price": 40.0, "output_price": 40.0, "composite_price": 40.0},
    {"model_id": "cogview-4", "model_name": "CogView-4", "provider": "zhipu", "is_reference": False, "score": 78.3, "generation_time": 15.2, "input_price": 20.0, "output_price": 20.0, "composite_price": 20.0},
]

MULTIMODAL_WORLD_MODELS = [
    {"model_id": "gemini-2.5-pro", "model_name": "Gemini 2.5 Pro", "provider": "google", "is_reference": True, "score": 84.2, "generation_time": 12.5, "input_price": 9.4, "output_price": 37.5, "composite_price": 16.4},
    {"model_id": "gpt-5.5", "model_name": "GPT-5.5", "provider": "openai", "is_reference": True, "score": 82.8, "generation_time": 10.3, "input_price": 14.5, "output_price": 58.0, "composite_price": 25.4},
    {"model_id": "qwen-vl-max", "model_name": "Qwen-VL-Max", "provider": "aliyun", "is_reference": False, "score": 79.5, "generation_time": 13.8, "input_price": 14.0, "output_price": 56.0, "composite_price": 24.5},
]

MULTIMODAL_VOICE_AV_MODELS = [
    {"model_id": "gpt-5.5", "model_name": "GPT-5.5", "provider": "openai", "is_reference": True, "score": 88.5, "generation_time": 3.2, "input_price": 14.5, "output_price": 58.0, "composite_price": 25.4},
    {"model_id": "gemini-2.5-pro", "model_name": "Gemini 2.5 Pro", "provider": "google", "is_reference": True, "score": 86.2, "generation_time": 2.8, "input_price": 9.4, "output_price": 37.5, "composite_price": 16.4},
    {"model_id": "claude-sonnet-4", "model_name": "Claude Sonnet 4", "provider": "anthropic", "is_reference": True, "score": 84.8, "generation_time": 2.5, "input_price": 21.0, "output_price": 105.0, "composite_price": 42.0},
]

MULTIMODAL_VOICE_CHAT_MODELS = [
    {"model_id": "gpt-5.5", "model_name": "GPT-5.5", "provider": "openai", "is_reference": True, "score": 89.1, "generation_time": 2.5, "input_price": 14.5, "output_price": 58.0, "composite_price": 25.4},
    {"model_id": "gemini-2.5-pro", "model_name": "Gemini 2.5 Pro", "provider": "google", "is_reference": True, "score": 87.3, "generation_time": 2.1, "input_price": 9.4, "output_price": 37.5, "composite_price": 16.4},
    {"model_id": "claude-sonnet-4", "model_name": "Claude Sonnet 4", "provider": "anthropic", "is_reference": True, "score": 85.6, "generation_time": 1.8, "input_price": 21.0, "output_price": 105.0, "composite_price": 42.0},
]

MULTIMODAL_TTS_MODELS = [
    {"model_id": "gpt-5.5-tts", "model_name": "GPT-5.5-TTS", "provider": "openai", "is_reference": True, "score": 90.2, "generation_time": 1.5, "input_price": 15.0, "output_price": 15.0, "composite_price": 15.0},
    {"model_id": "cosyvoice-2", "model_name": "CosyVoice 2", "provider": "aliyun", "is_reference": False, "score": 87.5, "generation_time": 1.2, "input_price": 8.0, "output_price": 8.0, "composite_price": 8.0},
    {"model_id": "fish-speech-2", "model_name": "Fish Speech 2", "provider": "fishaudio", "is_reference": False, "score": 84.3, "generation_time": 1.0, "input_price": 5.0, "output_price": 5.0, "composite_price": 5.0},
    {"model_id": "chat-tts", "model_name": "ChatTTS", "provider": "opensource", "is_reference": False, "score": 78.5, "generation_time": 0.8, "input_price": 2.0, "output_price": 2.0, "composite_price": 2.0},
]

BOARD_DEFINITIONS = [
    {"board_type": "overall", "name": "总排行榜", "parent": None, "models": OVERALL_MODELS},
    {"board_type": "reasoning_model", "name": "推理模型总排行榜", "parent": None, "models": REASONING_MODELS},
    {"board_type": "base_model", "name": "基础模型总排行榜", "parent": None, "models": BASE_MODELS},
    {"board_type": "reasoning_task", "name": "推理任务总排行榜", "parent": None, "models": REASONING_TASK_MODELS},
    {"board_type": "opensource", "name": "开源排行榜", "parent": None, "models": OPENSOURCE_MODELS},
    {"board_type": "multimodal", "name": "多模态榜", "parent": None, "models": MULTIMODAL_MODELS},
    {"board_type": "mm_vlm", "name": "SuperCLUE-VLM 视觉语言模型", "parent": "multimodal", "models": MULTIMODAL_VLM_MODELS},
    {"board_type": "mm_image", "name": "SuperCLUE-Image 文生图", "parent": "multimodal", "models": MULTIMODAL_IMAGE_MODELS},
    {"board_type": "mm_comic", "name": "SuperCLUE-ComicShorts AI漫剧", "parent": "multimodal", "models": MULTIMODAL_COMIC_MODELS},
    {"board_type": "mm_r2v", "name": "SuperCLUE-R2V 参考生视频", "parent": "multimodal", "models": MULTIMODAL_R2V_MODELS},
    {"board_type": "mm_i2v", "name": "SuperCLUE-I2V 图生视频", "parent": "multimodal", "models": MULTIMODAL_I2V_MODELS},
    {"board_type": "mm_edit", "name": "SuperCLUE-Edit 图像编辑", "parent": "multimodal", "models": MULTIMODAL_EDIT_MODELS},
    {"board_type": "mm_t2v", "name": "SuperCLUE-T2V 文生视频", "parent": "multimodal", "models": MULTIMODAL_T2V_MODELS},
    {"board_type": "mm_world", "name": "SuperCLUE-World 世界模型", "parent": "multimodal", "models": MULTIMODAL_WORLD_MODELS},
    {"board_type": "mm_voice_av", "name": "SuperCLUE-Voice 实时音视频", "parent": "multimodal", "models": MULTIMODAL_VOICE_AV_MODELS},
    {"board_type": "mm_voice_chat", "name": "SuperCLUE-Voice 实时语音交互", "parent": "multimodal", "models": MULTIMODAL_VOICE_CHAT_MODELS},
    {"board_type": "mm_tts", "name": "SuperCLUE-TTS 语音合成", "parent": "multimodal", "models": MULTIMODAL_TTS_MODELS},
    {"board_type": "mm_v", "name": "SuperCLUE-V 多模态理解", "parent": "multimodal", "models": MULTIMODAL_V_MODELS},
    {"board_type": "mm_vlr", "name": "SuperCLUE-VLR 视觉推理", "parent": "multimodal", "models": MULTIMODAL_VLR_MODELS},
]


class SuperCLUECrawler(BaseCrawler):
    def __init__(self):
        super().__init__(provider="superclue", base_url="https://superclueai.com")

    async def crawl(self) -> List[Dict[str, Any]]:
        now = datetime.now().strftime("%Y-%m-%d")
        results = []
        for board in BOARD_DEFINITIONS:
            for rank, m in enumerate(board["models"], 1):
                results.append({
                    "model_id": m["model_id"],
                    "model_name": m["model_name"],
                    "provider": m["provider"],
                    "board_type": board["board_type"],
                    "parent_board_type": board["parent"],
                    "rank": rank,
                    "score": m["score"],
                    "sub_scores": {},
                    "generation_time": m["generation_time"],
                    "input_price": m["input_price"],
                    "output_price": m["output_price"],
                    "composite_price": m["composite_price"],
                    "is_reference": m["is_reference"],
                    "period": PERIOD,
                    "source": "SuperCLUE",
                    "last_updated": now
                })
        return results
