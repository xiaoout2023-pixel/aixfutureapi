# 📦 AI模型库数据采集系统需求（Model Intelligence Hub Spec）

## 1. 项目目标

构建一个覆盖全球主流大模型与API服务商的统一模型库，用于支持以下核心能力：

- 💰 模型成本计算与对比
- 🤖 模型推荐与评分系统
- 🔀 API智能路由与多模型组合决策
- 📊 企业模型选型与分析工具

系统不只是“模型列表”，而是：

> Model Intelligence Layer（模型智能数据层）

---

## 2. 数据来源范围（必须覆盖）

### 2.1 官方模型厂商（Primary Source）

必须采集：

- OpenAI：https://platform.openai.com/docs/models
- Anthropic：https://docs.anthropic.com/
- Google Gemini：https://ai.google.dev/
- Meta LLaMA：https://llama.com/
- Mistral：https://mistral.ai/
- Cohere：https://cohere.com/
- Alibaba Qwen：https://tongyi.aliyun.com/
- Baidu ERNIE：https://cloud.baidu.com/
- AWS Bedrock：https://aws.amazon.com/bedrock/

---

### 2.2 模型聚合与市场平台（Market Source）

必须重点接入：

- OpenRouter：https://openrouter.ai/docs
- Together AI：https://www.together.ai/
- Fireworks AI：https://fireworks.ai/
- Replicate：https://replicate.com/

---

### 2.3 开源模型平台（Open Models）

- HuggingFace：https://huggingface.co/models
- GitHub Model Repos
- PapersWithCode（模型榜单）

---

## 3. 数据采集字段（统一Schema）

```json
{
  "model_id": "",
  "model_name": "",
  "provider": "",
  "source_type": "official | marketplace | open_source",

  "release_status": "preview | stable | deprecated",

  "capabilities": {
    "text": true,
    "vision": false,
    "audio": false,
    "code": false,
    "reasoning": false,
    "tool_use": false,
    "function_calling": false
  },

  "context_window": 0,

  "pricing": {
    "input_per_1m_tokens": 0,
    "output_per_1m_tokens": 0,
    "cached_input_price": 0,
    "batch_price": 0,
    "currency": "USD"
  },

  "performance": {
    "latency_ms": 0,
    "tokens_per_second": 0,
    "uptime": 0,
    "reliability_score": 0
  },

  "quality": {
    "mmlu_score": 0,
    "gsm8k_score": 0,
    "coding_score": 0,
    "human_preference_score": 0,
    "hallucination_rate": 0
  },

  "availability": {
    "region_restriction": false,
    "enterprise_only": false,
    "rate_limit": ""
  },

  "api": {
    "endpoint": "",
    "sdk_support": true,
    "openai_compatible": true
  },

  "metadata": {
    "release_date": "",
    "update_time": "",
    "tags": []
  },

  "source_urls": []
}
```
***


## 4. 数据采集方式（爬取策略）

### 4.1 官方API优先

适用：

- OpenAI
- Anthropic
- Cohere
- Mistral
- Together / Fireworks

方式：

- REST API调用
- 定时拉取 models + pricing
- 增量更新

***

### 4.2 网页爬虫

适用：

- Google Gemini
- Meta LLaMA
- Alibaba / Baidu
- Mistral docs

方式：

- HTML DOM解析
- table / JSON block提取
- fallback regex解析

***

### 4.3 OpenRouter / Marketplace API（关键数据源）

必须采集：

- 实际市场价格（market price）
- 多供应商同模型价格对比
- request volume（如可获取）
- latency stats（如可获取）
- provider list

方式：

- OpenRouter API
- marketplace aggregation API

***

### 4.4 开源模型解析

适用：

- HuggingFace model card
- GitHub repo

方式：

- HF API
- README + metadata parsing

***

## 5. 数据更新策略（关键机制）

### 5.1 更新频率

数据类型

频率

pricing（官方）

每6小时

marketplace价格

每3小时

新模型发现

每12小时

capability变化

每24小时

performance指标

每7天

open-source模型

每6小时

***

### 5.2 增量更新机制

- model\_id唯一索引
- hash diff检测变化
- 变化字段级更新

***

### 5.3 触发更新规则

- pricing变化 → 立即更新
- 新模型发布 → 即时插入
- provider新增 → 更新关联关系
- 性能指标变化 → 周期更新

***

## 6. 爬取执行规则

### 6.1 访问控制

- 单域名限速：1 request / 2s
- 最大并发：10
- 自动重试：3次 exponential backoff

***

### 6.2 数据解析规则

优先级：

1. API JSON（最高）
2. HTML结构化数据
3. Markdown / docs解析
4. regex fallback
5. LLM解析兜底

***

### 6.3 数据标准化

- 所有价格统一为 USD / 1M tokens
- capabilities统一标签体系
- model\_id统一规范：

```
provider:model_name:version

```

***

## 7. OpenRouter集成要求（必须）

必须实现：

- 同一模型多供应商价格对比
- marketplace价格覆盖官方价格
- provider维度性能数据聚合
- model routing基础数据来源

***

## 8. 数据用途定义（系统输出）

本模型库将直接服务：

### 8.1 成本系统

- 多模型成本计算
- prompt成本预估
- batch成本优化

### 8.2 推荐系统

- 模型评分
- 场景推荐（写作 / coding / agent / reasoning）

### 8.3 API路由系统

- lowest cost routing
- highest quality routing
- hybrid ensemble routing

### 8.4 企业选型系统

- 模型对比报告
- 性价比分析
- vendor选择建议

***

## 9. 风险控制

- 反爬限制识别与跳过
- API rate limit保护
- 数据缺失fallback机制
- 多源数据冲突优先级：

```
OpenRouter > 官方API > 文档页面 > 开源模型

```

***

## 10. 系统原则

- 数据必须可追溯（source\_url必填）
- 所有价格必须标准化
- 所有模型必须可对比
- 所有字段必须支持未来扩展

```
```

