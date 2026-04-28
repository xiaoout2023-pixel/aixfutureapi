# 模型库数据建设方案

## 一、现状分析

### 已有基础
- 数据库：Turso (libSQL/SQLite)，5张表（models, price_history, scenarios, scenario_steps, leaderboards）
- 爬虫：3个硬编码爬虫（OpenAI 8模型、Anthropic 4模型、Aliyun 5模型），共17个模型
- API：完整的模型查询/搜索/对比/成本计算接口
- 排行榜：SuperCLUE 排行榜数据（8个分类，80条数据）

### 核心差距（vs 需求文档）
| 维度 | 现状 | 需求 |
|------|------|------|
| 模型数量 | 17个 | 覆盖全球主流大模型（100+） |
| 数据来源 | 3家硬编码 | 9家官方 + 4家市场平台 + 开源平台 |
| Schema字段 | 11列，JSON存储 | 完整的capabilities/pricing/performance/quality/availability/api |
| 价格数据 | 仅官方定价 | 官方+市场价+多供应商对比 |
| 爬虫能力 | 全部硬编码 | API优先+网页爬虫+市场聚合 |
| 更新机制 | 手动触发 | 定时增量更新 |

---

## 二、技术方案

### 阶段一：Schema 升级（扩展 models 表）

**策略**：在现有 `models` 表基础上扩展 JSON 字段内容，不新增列，保持向下兼容。

当前 `capabilities` JSON 扩展为：
```json
{
  "text": true,
  "vision": false,
  "audio": false,
  "code": false,
  "reasoning": false,
  "tool_use": false,
  "function_calling": false,
  "image_generation": false,
  "video_understanding": false,
  "video_generation": false,
  "json_mode": false,
  "structured_output": false,
  "code_execution": false,
  "fine_tuning": false,
  "embedding": false,
  "context_length": 128000,
  "max_output_tokens": 4096,
  "reasoning_level": "high"
}
```

当前 `pricing` JSON 扩展为：
```json
{
  "input_per_1m_tokens": 2.50,
  "output_per_1m_tokens": 10.0,
  "cached_input_price": 1.25,
  "batch_input_price": 1.25,
  "batch_output_price": 5.0,
  "price_per_image": 0,
  "currency": "USD",
  "free_tier": false
}
```

新增 `performance` JSON 字段（存入现有 `scores` 字段中扩展）：
```json
{
  "reasoning_score": 90,
  "coding_score": 85,
  "speed_score": 75,
  "cost_efficiency_score": 95,
  "overall_score": 86.5,
  "latency_level": "medium",
  "throughput_level": "high"
}
```

新增 `availability` 和 `api_info` 存入 `source` 字段扩展：
```json
{
  "model_page": "",
  "api_docs": "",
  "pricing_page": "",
  "last_updated": "",
  "source_type": "official",
  "region_restriction": false,
  "enterprise_only": false,
  "openai_compatible": true,
  "sdk_support": true
}
```

**新增表 `model_marketplace`**：多供应商价格对比
```sql
CREATE TABLE model_marketplace (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT NOT NULL,
    marketplace TEXT NOT NULL,
    marketplace_model_id TEXT,
    input_price REAL,
    output_price REAL,
    latency_ms INTEGER,
    uptime REAL,
    availability TEXT,
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(model_id, marketplace)
);
```

### 阶段二：爬虫实现（按数据源优先级）

#### 第一批：官方API数据源（数据最可靠）
1. **OpenRouter 爬虫** - 关键数据源，一次获取所有模型+多供应商价格
   - API: `https://openrouter.ai/api/v1/models`
   - 覆盖：100+ 模型，含市场价格、延迟、供应商列表
2. **Google Gemini 爬虫** - 网页爬虫
   - 来源：https://ai.google.dev/pricing
3. **Mistral 爬虫** - API + 网页
   - API: `https://api.mistral.ai/v1/models`
4. **Cohere 爬虫** - API
   - API: `https://api.cohere.ai/v1/models`

#### 第二批：国内厂商
5. **百度 ERNIE 爬虫** - 网页爬虫
6. **智谱 GLM 爬虫** - 网页爬虫
7. **DeepSeek 爬虫** - API
8. **月之暗面 Kimi 爬虫** - 网页爬虫
9. **MiniMax 爬虫** - 网页爬虫

#### 第三批：市场平台
10. **Together AI 爬虫** - API
11. **Fireworks AI 爬虫** - API
12. **Replicate 爬虫** - API

#### 第四批：开源平台
13. **HuggingFace 爬虫** - HF API

### 阶段三：种子数据初始化

基于 OpenRouter API + 各厂商公开数据，构建初始模型库：
- 目标：100+ 模型，覆盖 15+ 供应商
- 包含完整的 capabilities、pricing、performance 数据
- 包含 marketplace 多供应商价格对比

### 阶段四：API 接口扩展

新增/修改接口：
1. `GET /api/models` - 扩展返回字段（performance, availability, api_info）
2. `GET /api/models/{model_id}/marketplace` - 获取模型多供应商价格对比
3. `GET /api/marketplace/compare` - 跨供应商价格对比
4. `GET /api/providers/{provider}/models` - 按供应商获取模型列表

---

## 三、执行步骤

### Step 1: 数据库 Schema 升级
- 修改 `db/init_db.py`，新增 `model_marketplace` 表
- 修改 `db/repository.py`，新增 marketplace 相关方法
- 执行数据库初始化

### Step 2: 实现 OpenRouter 爬虫（核心）
- 新建 `crawler/openrouter.py`
- 调用 OpenRouter API 获取全量模型数据
- 解析模型信息、价格、供应商列表
- 同时写入 `models` 表和 `model_marketplace` 表

### Step 3: 实现其他官方API爬虫
- `crawler/google_gemini.py`
- `crawler/mistral.py`
- `crawler/cohere.py`

### Step 4: 实现国内厂商爬虫
- `crawler/baidu.py`
- `crawler/zhipu.py`
- `crawler/deepseek.py`
- `crawler/moonshot.py`
- `crawler/minimax.py`

### Step 5: 实现市场平台爬虫
- `crawler/together.py`
- `crawler/fireworks.py`
- `crawler/replicate.py`

### Step 6: 种子数据初始化
- 运行 OpenRouter 爬虫获取全量数据
- 运行各厂商爬虫补充官方定价
- 验证数据完整性

### Step 7: API 接口扩展
- 扩展模型返回字段
- 新增 marketplace 接口
- 更新接口文档

### Step 8: 测试与验证
- 测试所有新增接口
- 验证数据完整性
- 更新 docs.html 文档

---

## 四、关键设计决策

1. **Schema 扩展策略**：在现有 JSON 字段内扩展，不新增列，保持向下兼容
2. **OpenRouter 优先**：一次 API 调用获取 100+ 模型数据，是最快建立模型库的方式
3. **多源数据合并**：OpenRouter 数据作为基础，各厂商官方数据覆盖补充
4. **marketplace 独立表**：多供应商价格对比需要独立存储，支持同一模型不同供应商的价格/性能对比
5. **爬虫分级**：API 优先 > 网页爬虫 > 硬编码兜底
