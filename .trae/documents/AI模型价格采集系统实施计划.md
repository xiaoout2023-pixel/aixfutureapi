# AI模型价格采集系统 - 实施计划

## 项目概述

构建一个每日自动爬取AI模型价格并提供API查询对比的系统。

- **技术栈**: Python + FastAPI
- **部署**: Vercel (Serverless)
- **存储**: models.json + Git (只读)
- **定时任务**: GitHub Actions (每日3:00 AM UTC)
- **MVP厂商**: OpenAI + Anthropic + 阿里云

---

## 实施步骤

### 阶段1: 项目初始化

1. 创建项目目录结构
2. 初始化 `requirements.txt` (fastapi, httpx, beautifulsoup4, pydantic)
3. 创建 `vercel.json` 配置
4. 创建 `api/models.json` 初始空数据
5. 创建 `.gitignore`

### 阶段2: FastAPI核心

1. 创建 `api/main.py`
   - 实现5个API路由
   - 实现筛选排序逻辑
   - 实现标准化响应格式
   - 加载并缓存 models.json

### 阶段3: 爬虫基类

1. 创建 `crawler/base.py`
   - 定义爬虫接口
   - 实现价格单位统一 (/1K tokens)
   - 实现模型ID标准化
   - 实现错误处理和重试机制

### 阶段4: MVP爬虫实现

1. **OpenAI爬虫** (`crawler/openai.py`)
   - 爬取 https://openai.com/pricing
   - 提取 gpt-4o, gpt-4.1, o-series 等模型
   - 提取 context_length, pricing, features

2. **Anthropic爬虫** (`crawler/anthropic.py`)
   - 爬取 https://www.anthropic.com/pricing
   - 提取 claude-3-opus, claude-3-sonnet, claude-3-haiku
   - 提取 context_length, pricing

3. **阿里云爬虫** (`crawler/aliyun.py`)
   - 爬取 https://dashscope.aliyun.com/pricing
   - 提取 qwen-max, qwen-plus, qwen-turbo 等
   - 价格转换为 USD

### 阶段5: 数据合并与写入

1. 创建 `crawler/run_all.py`
   - 按顺序执行所有爬虫
   - 合并数据到 models.json
   - 添加更新时间戳
   - 错误处理（单个爬虫失败不影响其他）

### 阶段6: GitHub Actions配置

1. 创建 `.github/workflows/update-models.yml`
   - 每日3:00 AM UTC触发
   - 支持手动触发 (workflow_dispatch)
   - 运行爬虫
   - 检测变更并自动 commit & push
   - 使用 PAT (Personal Access Token) 推送

### 阶段7: Vercel部署配置

1. 创建 `vercel.json`
   - 配置API路由
   - 配置Python运行时
   - 设置环境变量

### 阶段8: 本地测试

1. 测试爬虫功能 (模拟数据)
2. 测试API端点
3. 验证筛选排序功能
4. 验证对比功能
5. 测试GitHub Actions工作流 (手动触发)

---

## 目录结构

```
/
├── api/
│   ├── main.py                   # FastAPI应用
│   └── models.json               # 模型数据（只读）
├── crawler/
│   ├── __init__.py
│   ├── base.py                   # 爬虫基类
│   ├── openai.py                 # OpenAI爬虫
│   ├── anthropic.py              # Anthropic爬虫
│   ├── aliyun.py                 # 阿里云爬虫
│   └── run_all.py                # 统一执行脚本
├── .github/workflows/
│   └── update-models.yml         # GitHub Actions
├── requirements.txt
├── vercel.json
└── .gitignore
```

---

## 关键设计决策

1. **数据存储**: models.json 存储在代码仓库中，Vercel只读
2. **价格单位**: 统一为 USD per 1K tokens
3. **模型ID**: 格式为 `provider/model_name`
4. **API响应**: 标准RESTful格式 `{code, message, data}`
5. **错误处理**: 单个爬虫失败不影响整体，记录错误日志
6. **CORS**: MVP阶段允许所有来源
7. **认证**: MVP阶段无需API Key

---

## API接口清单

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/models | 获取模型列表（支持筛选排序） |
| GET | /api/compare | 模型对比 |
| GET | /api/providers | 获取厂商列表 |
| GET | /api/models/{provider}/{model} | 获取单个模型详情 |
| GET | /api/status | 数据更新状态 |

---

## 数据结构

```json
{
  "id": "openai/gpt-4o",
  "provider": "openai",
  "model": "gpt-4o",
  "context_length": 128000,
  "pricing": {
    "input_per_1k_tokens": 0.005,
    "output_per_1k_tokens": 0.015,
    "currency": "USD"
  },
  "features": {
    "vision": true,
    "tool_use": true,
    "audio": false,
    "function_calling": true
  },
  "type": "multimodal",
  "updated_at": "2026-04-25",
  "source": "https://openai.com/pricing"
}
```

---

## 风险与注意事项

1. **Vercel冷启动**: 首次请求可能较慢，可考虑添加健康检查
2. **爬虫稳定性**: 厂商网页结构变化可能导致爬虫失效，需要定期维护
3. **价格精度**: 部分厂商价格不是按token计算，需要合理转换
4. **GitHub Actions频率**: 免费额度每月2000分钟，每日运行完全足够
5. **Git推送**: 需要使用PAT，需在仓库设置中添加Secret
