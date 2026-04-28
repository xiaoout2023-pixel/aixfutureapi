import json
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.turso import TursoDB
from db.repository import ModelRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SEED_DATA = {
    "general_overall": [
        {"rank": 1, "model_name": "Claude-Opus-4.6", "organization": "Anthropic", "score": 76.82, "is_opensource": 0, "is_domestic": 0, "score_details": {"数学推理": 78.5, "科学推理": 80.2, "代码生成": 82.1, "精确指令遵循": 75.3, "幻觉控制": 72.8, "智能体": 76.0}},
        {"rank": 2, "model_name": "Gemini-3.1-Pro-Preview", "organization": "Google", "score": 74.56, "is_opensource": 0, "is_domestic": 0, "score_details": {"数学推理": 80.1, "科学推理": 78.9, "代码生成": 76.5, "精确指令遵循": 70.2, "幻觉控制": 68.5, "智能体": 73.6}},
        {"rank": 3, "model_name": "GPT-5.4", "organization": "OpenAI", "score": 72.48, "is_opensource": 0, "is_domestic": 0, "score_details": {"数学推理": 77.3, "科学推理": 76.8, "代码生成": 79.5, "精确指令遵循": 68.9, "幻觉控制": 65.2, "智能体": 67.2}},
        {"rank": 4, "model_name": "Doubao-Seed-2.0-pro", "organization": "字节跳动", "score": 71.53, "is_opensource": 0, "is_domestic": 1, "score_details": {"数学推理": 72.5, "科学推理": 70.8, "代码生成": 74.2, "精确指令遵循": 68.5, "幻觉控制": 66.3, "智能体": 76.8}},
        {"rank": 5, "model_name": "DeepSeek-V4-Pro", "organization": "深度求索", "score": 70.98, "is_opensource": 0, "is_domestic": 1, "score_details": {"数学推理": 78.2, "科学推理": 75.6, "代码生成": 76.8, "精确指令遵循": 62.5, "幻觉控制": 60.8, "智能体": 71.8}},
        {"rank": 6, "model_name": "Qwen3.6-Plus", "organization": "阿里巴巴", "score": 69.85, "is_opensource": 0, "is_domestic": 1, "score_details": {"数学推理": 73.5, "科学推理": 71.2, "代码生成": 72.8, "精确指令遵循": 65.3, "幻觉控制": 64.8, "智能体": 71.5}},
        {"rank": 7, "model_name": "ERNIE-5.0", "organization": "百度", "score": 68.72, "is_opensource": 0, "is_domestic": 1, "score_details": {"数学推理": 70.5, "科学推理": 68.8, "代码生成": 71.2, "精确指令遵循": 66.5, "幻觉控制": 65.2, "智能体": 70.1}},
        {"rank": 8, "model_name": "GLM-5.1", "organization": "智谱AI", "score": 67.35, "is_opensource": 0, "is_domestic": 1, "score_details": {"数学推理": 68.5, "科学推理": 66.8, "代码生成": 72.5, "精确指令遵循": 63.2, "幻觉控制": 62.8, "智能体": 70.8}},
        {"rank": 9, "model_name": "o4-mini", "organization": "OpenAI", "score": 65.91, "is_opensource": 0, "is_domestic": 0, "score_details": {"数学推理": 72.8, "科学推理": 70.5, "代码生成": 68.2, "精确指令遵循": 60.5, "幻觉控制": 58.2, "智能体": 65.2}},
        {"rank": 10, "model_name": "Claude-Sonnet-4.5-Reasoning", "organization": "Anthropic", "score": 65.62, "is_opensource": 0, "is_domestic": 0, "score_details": {"数学推理": 70.2, "科学推理": 68.5, "代码生成": 72.8, "精确指令遵循": 62.8, "幻觉控制": 58.5, "智能体": 61.2}},
        {"rank": 11, "model_name": "MiMo-V2-Pro", "organization": "小米", "score": 60.67, "is_opensource": 0, "is_domestic": 1, "score_details": {"数学推理": 84.03, "科学推理": 58.2, "代码生成": 55.8, "精确指令遵循": 50.2, "幻觉控制": 52.5, "智能体": 63.2}},
        {"rank": 12, "model_name": "Kimi-K2.5-Thinking", "organization": "月之暗面", "score": 59.85, "is_opensource": 1, "is_domestic": 1, "score_details": {"数学推理": 65.2, "科学推理": 62.8, "代码生成": 60.5, "精确指令遵循": 52.8, "幻觉控制": 55.2, "智能体": 62.5}},
        {"rank": 13, "model_name": "Qwen3.5-397B-A17B-Thinking", "organization": "阿里巴巴", "score": 58.72, "is_opensource": 1, "is_domestic": 1, "score_details": {"数学推理": 63.5, "科学推理": 60.8, "代码生成": 62.2, "精确指令遵循": 50.5, "幻觉控制": 53.8, "智能体": 61.5}},
        {"rank": 14, "model_name": "openPangu-Ultra-MoE-718B", "organization": "华为", "score": 57.53, "is_opensource": 1, "is_domestic": 1, "score_details": {"数学推理": 60.2, "科学推理": 58.5, "代码生成": 55.8, "精确指令遵循": 52.2, "幻觉控制": 58.5, "智能体": 60.0}},
        {"rank": 15, "model_name": "DeepSeek-V3.2-Exp-Thinking", "organization": "深度求索", "score": 62.62, "is_opensource": 1, "is_domestic": 1, "score_details": {"数学推理": 70.5, "科学推理": 68.2, "代码生成": 65.8, "精确指令遵循": 55.2, "幻觉控制": 52.8, "智能体": 63.2}},
    ],
    "general_reasoning": [
        {"rank": 1, "model_name": "Claude-Opus-4.6", "organization": "Anthropic", "score": 80.27, "is_opensource": 0, "is_domestic": 0, "score_details": {"数学推理": 78.5, "科学推理": 80.2, "代码生成": 82.1}},
        {"rank": 2, "model_name": "Gemini-3.1-Pro-Preview", "organization": "Google", "score": 78.50, "is_opensource": 0, "is_domestic": 0, "score_details": {"数学推理": 80.1, "科学推理": 78.9, "代码生成": 76.5}},
        {"rank": 3, "model_name": "GPT-5.4", "organization": "OpenAI", "score": 77.87, "is_opensource": 0, "is_domestic": 0, "score_details": {"数学推理": 77.3, "科学推理": 76.8, "代码生成": 79.5}},
        {"rank": 4, "model_name": "DeepSeek-V4-Pro", "organization": "深度求索", "score": 76.87, "is_opensource": 0, "is_domestic": 1, "score_details": {"数学推理": 78.2, "科学推理": 75.6, "代码生成": 76.8}},
        {"rank": 5, "model_name": "Doubao-Seed-2.0-pro", "organization": "字节跳动", "score": 72.50, "is_opensource": 0, "is_domestic": 1, "score_details": {"数学推理": 72.5, "科学推理": 70.8, "代码生成": 74.2}},
        {"rank": 6, "model_name": "MiMo-V2-Pro", "organization": "小米", "score": 66.01, "is_opensource": 0, "is_domestic": 1, "score_details": {"数学推理": 84.03, "科学推理": 58.2, "代码生成": 55.8}},
        {"rank": 7, "model_name": "Qwen3.6-Plus", "organization": "阿里巴巴", "score": 72.50, "is_opensource": 0, "is_domestic": 1, "score_details": {"数学推理": 73.5, "科学推理": 71.2, "代码生成": 72.8}},
        {"rank": 8, "model_name": "ERNIE-5.0", "organization": "百度", "score": 70.17, "is_opensource": 0, "is_domestic": 1, "score_details": {"数学推理": 70.5, "科学推理": 68.8, "代码生成": 71.2}},
        {"rank": 9, "model_name": "DeepSeek-V3.2-Exp-Thinking", "organization": "深度求索", "score": 68.17, "is_opensource": 1, "is_domestic": 1, "score_details": {"数学推理": 70.5, "科学推理": 68.2, "代码生成": 65.8}},
        {"rank": 10, "model_name": "Kimi-K2.5-Thinking", "organization": "月之暗面", "score": 62.83, "is_opensource": 1, "is_domestic": 1, "score_details": {"数学推理": 65.2, "科学推理": 62.8, "代码生成": 60.5}},
    ],
    "general_base": [
        {"rank": 1, "model_name": "Doubao-Seed-2.0-pro", "organization": "字节跳动", "score": 70.53, "is_opensource": 0, "is_domestic": 1, "score_details": {"精确指令遵循": 68.5, "幻觉控制": 66.3, "智能体": 76.8}},
        {"rank": 2, "model_name": "Claude-Opus-4.6", "organization": "Anthropic", "score": 74.70, "is_opensource": 0, "is_domestic": 0, "score_details": {"精确指令遵循": 75.3, "幻觉控制": 72.8, "智能体": 76.0}},
        {"rank": 3, "model_name": "Gemini-3.1-Pro-Preview", "organization": "Google", "score": 70.77, "is_opensource": 0, "is_domestic": 0, "score_details": {"精确指令遵循": 70.2, "幻觉控制": 68.5, "智能体": 73.6}},
        {"rank": 4, "model_name": "GPT-5.4", "organization": "OpenAI", "score": 67.10, "is_opensource": 0, "is_domestic": 0, "score_details": {"精确指令遵循": 68.9, "幻觉控制": 65.2, "智能体": 67.2}},
        {"rank": 5, "model_name": "Qwen3.6-Plus", "organization": "阿里巴巴", "score": 67.20, "is_opensource": 0, "is_domestic": 1, "score_details": {"精确指令遵循": 65.3, "幻觉控制": 64.8, "智能体": 71.5}},
        {"rank": 6, "model_name": "ERNIE-5.0", "organization": "百度", "score": 67.27, "is_opensource": 0, "is_domestic": 1, "score_details": {"精确指令遵循": 66.5, "幻觉控制": 65.2, "智能体": 70.1}},
        {"rank": 7, "model_name": "GLM-5.1", "organization": "智谱AI", "score": 65.60, "is_opensource": 0, "is_domestic": 1, "score_details": {"精确指令遵循": 63.2, "幻觉控制": 62.8, "智能体": 70.8}},
        {"rank": 8, "model_name": "DeepSeek-V4-Pro", "organization": "深度求索", "score": 65.03, "is_opensource": 0, "is_domestic": 1, "score_details": {"精确指令遵循": 62.5, "幻觉控制": 60.8, "智能体": 71.8}},
    ],
    "general_reasoning_task": [
        {"rank": 1, "model_name": "Claude-Opus-4.6", "organization": "Anthropic", "score": 80.27, "is_opensource": 0, "is_domestic": 0, "score_details": {"数学推理": 78.5, "科学推理": 80.2, "代码生成": 82.1}},
        {"rank": 2, "model_name": "Gemini-3.1-Pro-Preview", "organization": "Google", "score": 78.50, "is_opensource": 0, "is_domestic": 0, "score_details": {"数学推理": 80.1, "科学推理": 78.9, "代码生成": 76.5}},
        {"rank": 3, "model_name": "GPT-5.4", "organization": "OpenAI", "score": 77.87, "is_opensource": 0, "is_domestic": 0, "score_details": {"数学推理": 77.3, "科学推理": 76.8, "代码生成": 79.5}},
        {"rank": 4, "model_name": "DeepSeek-V4-Pro", "organization": "深度求索", "score": 76.87, "is_opensource": 0, "is_domestic": 1, "score_details": {"数学推理": 78.2, "科学推理": 75.6, "代码生成": 76.8}},
        {"rank": 5, "model_name": "Doubao-Seed-2.0-pro", "organization": "字节跳动", "score": 72.50, "is_opensource": 0, "is_domestic": 1, "score_details": {"数学推理": 72.5, "科学推理": 70.8, "代码生成": 74.2}},
        {"rank": 6, "model_name": "MiMo-V2-Pro", "organization": "小米", "score": 66.01, "is_opensource": 0, "is_domestic": 1, "score_details": {"数学推理": 84.03, "科学推理": 58.2, "代码生成": 55.8}},
    ],
    "general_opensource": [
        {"rank": 1, "model_name": "DeepSeek-V3.2-Exp-Thinking", "organization": "深度求索", "score": 62.62, "is_opensource": 1, "is_domestic": 1, "score_details": {"数学推理": 70.5, "科学推理": 68.2, "代码生成": 65.8, "精确指令遵循": 55.2, "幻觉控制": 52.8, "智能体": 63.2}},
        {"rank": 2, "model_name": "Kimi-K2.5-Thinking", "organization": "月之暗面", "score": 59.85, "is_opensource": 1, "is_domestic": 1, "score_details": {"数学推理": 65.2, "科学推理": 62.8, "代码生成": 60.5, "精确指令遵循": 52.8, "幻觉控制": 55.2, "智能体": 62.5}},
        {"rank": 3, "model_name": "Qwen3.5-397B-A17B-Thinking", "organization": "阿里巴巴", "score": 58.72, "is_opensource": 1, "is_domestic": 1, "score_details": {"数学推理": 63.5, "科学推理": 60.8, "代码生成": 62.2, "精确指令遵循": 50.5, "幻觉控制": 53.8, "智能体": 61.5}},
        {"rank": 4, "model_name": "openPangu-Ultra-MoE-718B", "organization": "华为", "score": 57.53, "is_opensource": 1, "is_domestic": 1, "score_details": {"数学推理": 60.2, "科学推理": 58.5, "代码生成": 55.8, "精确指令遵循": 52.2, "幻觉控制": 58.5, "智能体": 60.0}},
        {"rank": 5, "model_name": "Qwen3-235B-A22B-Thinking", "organization": "阿里巴巴", "score": 57.73, "is_opensource": 1, "is_domestic": 1, "score_details": {"数学推理": 62.8, "科学推理": 60.2, "代码生成": 58.5, "精确指令遵循": 50.8, "幻觉控制": 52.5, "智能体": 61.8}},
        {"rank": 6, "model_name": "gpt-oss-120b", "organization": "OpenAI", "score": 53.05, "is_opensource": 1, "is_domestic": 0, "score_details": {"数学推理": 58.2, "科学推理": 56.5, "代码生成": 52.8, "精确指令遵循": 48.5, "幻觉控制": 50.2, "智能体": 58.0}},
        {"rank": 7, "model_name": "Llama-4-Maverick", "organization": "Meta", "score": 52.80, "is_opensource": 1, "is_domestic": 0, "score_details": {"数学推理": 55.2, "科学推理": 53.8, "代码生成": 56.5, "精确指令遵循": 46.8, "幻觉控制": 48.5, "智能体": 56.0}},
        {"rank": 8, "model_name": "MiMo-V2-Flash", "organization": "小米", "score": 49.97, "is_opensource": 1, "is_domestic": 1, "score_details": {"数学推理": 52.8, "科学推理": 48.5, "代码生成": 50.2, "精确指令遵循": 45.5, "幻觉控制": 47.8, "智能体": 54.5}},
    ],
    "multimodal_vlm": [
        {"rank": 1, "model_name": "Gemini-2.5-Pro", "organization": "Google", "score": 74.99, "is_opensource": 0, "is_domestic": 0, "score_details": {"基础认知": 82.5, "视觉推理": 78.8, "视觉应用": 63.7}},
        {"rank": 2, "model_name": "GPT-5", "organization": "OpenAI", "score": 68.59, "is_opensource": 0, "is_domestic": 0, "score_details": {"基础认知": 78.2, "视觉推理": 72.5, "视觉应用": 55.1}},
        {"rank": 3, "model_name": "SenseNova-V6.5-Pro", "organization": "商汤", "score": 75.35, "is_opensource": 0, "is_domestic": 1, "score_details": {"基础认知": 80.2, "视觉推理": 76.8, "视觉应用": 69.1}},
        {"rank": 4, "model_name": "Doubao-Seed-1.6-thinking", "organization": "字节跳动", "score": 66.47, "is_opensource": 0, "is_domestic": 1, "score_details": {"基础认知": 75.8, "视觉推理": 68.2, "视觉应用": 55.4}},
        {"rank": 5, "model_name": "ERNIE-4.5-Turbo-VL", "organization": "百度", "score": 66.47, "is_opensource": 0, "is_domestic": 1, "score_details": {"基础认知": 76.5, "视觉推理": 67.8, "视觉应用": 55.1}},
        {"rank": 6, "model_name": "Hunyuan-t1-vision", "organization": "腾讯", "score": 63.78, "is_opensource": 0, "is_domestic": 1, "score_details": {"基础认知": 72.5, "视觉推理": 65.2, "视觉应用": 53.6}},
        {"rank": 7, "model_name": "Qwen-V1-Max", "organization": "阿里巴巴", "score": 62.50, "is_opensource": 0, "is_domestic": 1, "score_details": {"基础认知": 70.8, "视觉推理": 63.5, "视觉应用": 53.2}},
        {"rank": 8, "model_name": "Claude-Opus-4.1", "organization": "Anthropic", "score": 65.80, "is_opensource": 0, "is_domestic": 0, "score_details": {"基础认知": 75.2, "视觉推理": 68.5, "视觉应用": 53.7}},
    ],
    "multimodal_image": [
        {"rank": 1, "model_name": "Gemini-3.1-Flash-Image-Preview", "organization": "Google", "score": 1393.7, "is_opensource": 0, "is_domestic": 0, "score_details": {"排位分": 1393.7, "95%CI": "+23.7/-21.4", "投票数": 4435}},
        {"rank": 2, "model_name": "Gemini-3-Pro-Image-Preview", "organization": "Google", "score": 1296.1, "is_opensource": 0, "is_domestic": 0, "score_details": {"排位分": 1296.1, "95%CI": "+32.1/-32.6", "投票数": 1805}},
        {"rank": 3, "model_name": "GPT-Image-1.5", "organization": "OpenAI", "score": 1220.5, "is_opensource": 0, "is_domestic": 0, "score_details": {"排位分": 1220.5, "95%CI": "+22.5/-22.2", "投票数": 3043}},
        {"rank": 4, "model_name": "Seedream-4.5", "organization": "字节跳动", "score": 1155.2, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1155.2, "95%CI": "+27.5/-29.0", "投票数": 1672}},
        {"rank": 5, "model_name": "Qwen-Image-2.0-Pro", "organization": "阿里巴巴", "score": 1141.4, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1141.4, "95%CI": "+19.0/-22.8", "投票数": 3022}},
        {"rank": 6, "model_name": "HunyuanImage-3.0", "organization": "腾讯", "score": 1081.0, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1081.0, "95%CI": "+28.1/-26.5", "投票数": 1723}},
        {"rank": 7, "model_name": "Seedream-4.0", "organization": "字节跳动", "score": 1073.3, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1073.3, "95%CI": "+26.7/-27.3", "投票数": 1714}},
        {"rank": 8, "model_name": "Seedream-3.0", "organization": "字节跳动", "score": 1053.6, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1053.6, "95%CI": "+25.1/-26.6", "投票数": 1744}},
        {"rank": 9, "model_name": "Wan-2.6", "organization": "阿里巴巴", "score": 1029.1, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1029.1, "95%CI": "+24.8/-24.4", "投票数": 2035}},
        {"rank": 10, "model_name": "GPT-Image-1", "organization": "OpenAI", "score": 941.6, "is_opensource": 0, "is_domestic": 0, "score_details": {"排位分": 941.6, "95%CI": "+27.9/-28.5", "投票数": 1445}},
    ],
    "multimodal_t2v": [
        {"rank": 1, "model_name": "Seedance-2.0", "organization": "字节跳动", "score": 1321.9, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1321.9, "95%CI": "+28.7/-28.8", "投票数": 2005}},
        {"rank": 2, "model_name": "可灵-3.0", "organization": "快手科技", "score": 1265.3, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1265.3, "95%CI": "+31.5/-32.1", "投票数": 1479}},
        {"rank": 3, "model_name": "Veo-3.1", "organization": "Google", "score": 1220.1, "is_opensource": 0, "is_domestic": 0, "score_details": {"排位分": 1220.1, "95%CI": "+28.1/-26.1", "投票数": 2283}},
        {"rank": 4, "model_name": "PixVerse-V6", "organization": "爱诗科技", "score": 1168.2, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1168.2, "95%CI": "+89.0/-75.5", "投票数": 192}},
        {"rank": 5, "model_name": "veo-3.0-generate-preview", "organization": "Google", "score": 1117.2, "is_opensource": 0, "is_domestic": 0, "score_details": {"排位分": 1117.2, "95%CI": "+21.0/-21.2", "投票数": 3822}},
        {"rank": 6, "model_name": "Luma-Ray-3", "organization": "Luma AI", "score": 1086.1, "is_opensource": 0, "is_domestic": 0, "score_details": {"排位分": 1086.1, "95%CI": "+25.9/-24.0", "投票数": 2023}},
        {"rank": 7, "model_name": "Vidu-Q3", "organization": "生数科技", "score": 1079.7, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1079.7, "95%CI": "+28.2/-27.6", "投票数": 1606}},
        {"rank": 8, "model_name": "Hailuo-02", "organization": "MiniMax", "score": 1054.8, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1054.8, "95%CI": "+22.5/-21.4", "投票数": 3462}},
        {"rank": 9, "model_name": "可灵-2.5-Turbo", "organization": "快手科技", "score": 1049.0, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1049.0, "95%CI": "+24.7/-26.4", "投票数": 1917}},
        {"rank": 10, "model_name": "Wan-2.6", "organization": "阿里巴巴", "score": 1044.7, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1044.7, "95%CI": "+23.7/-23.3", "投票数": 2480}},
    ],
    "multimodal_i2v": [
        {"rank": 1, "model_name": "Veo-3.1", "organization": "Google", "score": 1280.5, "is_opensource": 0, "is_domestic": 0, "score_details": {"排位分": 1280.5}},
        {"rank": 2, "model_name": "Seedance-2.0-I2V", "organization": "字节跳动", "score": 1250.2, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1250.2}},
        {"rank": 3, "model_name": "可灵-3.0-I2V", "organization": "快手科技", "score": 1200.8, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1200.8}},
        {"rank": 4, "model_name": "PixVerse-V6-I2V", "organization": "爱诗科技", "score": 1100.5, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1100.5}},
        {"rank": 5, "model_name": "Vidu-Q3-I2V", "organization": "生数科技", "score": 1050.3, "is_opensource": 0, "is_domestic": 1, "score_details": {"排位分": 1050.3}},
    ],
}


async def seed_leaderboard_data():
    logger.info("Seeding leaderboard data...")
    db = TursoDB()
    repo = ModelRepository(db)

    total = 0
    for category, entries in SEED_DATA.items():
        for entry in entries:
            try:
                await repo.save_leaderboard_entry({
                    "category": category,
                    "rank": entry["rank"],
                    "model_name": entry["model_name"],
                    "organization": entry["organization"],
                    "score": entry["score"],
                    "score_details": json.dumps(entry.get("score_details", {}), ensure_ascii=False),
                    "is_opensource": entry.get("is_opensource", 0),
                    "is_domestic": entry.get("is_domestic", 1),
                    "release_date": entry.get("release_date", ""),
                })
                total += 1
            except Exception as e:
                logger.error(f"Error saving entry {category}/{entry['model_name']}: {e}")

    logger.info(f"Seeded {total} leaderboard entries")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_leaderboard_data())
