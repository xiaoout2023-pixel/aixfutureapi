# API系统重构计划 (v0.2.0)

## 项目目标

构建一个完整的**AI模型库**，包含：

1. 完整的模型信息（能力、价格、评分、标签）
2. 成本计算功能
3. 每日自动更新
4. 部署在Vercel上

***

## 核心决策

### 1. 数据库方案：Turso (SQLite边缘数据库)

**选择理由**：

* 真正SQLite，零学习成本

* 完美兼容Vercel Serverless

* 免费额度充足（9GB存储、50亿行读取/月）

* 支持完整SQL查询（筛选、排序、统计）

* 边缘部署，全球低延迟

**对比分析**：

| 方案        | 优点              | 缺点         | Vercel兼容 | 推荐度       |
| --------- | --------------- | ---------- | -------- | --------- |
| JSON文件    | 极简、零依赖          | 无查询能力、并发风险 | 只读       | ⭐⭐        |
| SQLite本地  | 轻量              | 文件系统只读     | ❌        | ⭐         |
| Vercel KV | 官方支持            | 免费额度有限     | ✅        | ⭐⭐⭐⭐      |
| **Turso** | **真正SQLite、免费** | **需注册**    | **✅**    | **⭐⭐⭐⭐⭐** |
| Supabase  | 功能全             | 略重         | ✅        | ⭐⭐⭐⭐      |

### 2. 爬虫方案：混合数据源

**当前问题**：

* OpenAI返回403

* 新增字段（scores、tags、release\_date）无法直接爬取

**解决方案**：

```
方案：混合数据源
├── 模型基本信息：官方API/文档
│   ├── OpenAI: GET /v1/models
│   ├── Anthropic: 官方文档
│   └── 其他厂商
├── 价格数据：网页爬取
│   ├── 成功→更新
│   └── 失败→保留上次有效数据
└── 评分数据
    ├── 初期：手动维护（基于LMSYS等榜单）
    └── 后期：自动对接LMSYS API
```

***

## 实施步骤

### 阶段1: 数据库设置

1. **注册Turso账号**

   * 访问 <https://turso.tech>

   * 创建免费账号

   * 创建数据库：`ai-models-db`

   * 获取数据库URL和Token

   * URL：libsql://ai-models-db-xiaoout.aws-us-west-2.turso.io

   * Token：eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NzcxMzk0NTcsImlkIjoiMDE5ZGM1YzMtYjEwMS03ZmI3LTk2MTktMjcxMTQ5MTc0NjMxIiwicmlkIjoiMWRiYjJmYmQtYzBiOS00MGVmLTk1OGYtODMxMDQ5OGI3MGEwIn0.ZJPCre8vUElMfKyEJITI6cdLcj9yDwjGxd49FmoXYBe5VlaVbs4LTKYffeTzbbKZGYOB8KCd-ubqrzjOs6mGCg

2. **安装依赖**

   ```
   pip install libsql-client
   ```

3. **初始化数据库**

   * 创建models表

   * 创建price\_history表

   * 插入初始数据

### 阶段2: 数据结构重构

**新数据结构**（完全按需求文档）：

```json
{
  "model_id": "gpt-4o",
  "model_name": "GPT-4o",
  "provider": "openai",
  "release_date": "2024-05-13",
  "status": "active",
  
  "capabilities": {
    "text_generation": true,
    "code_generation": true,
    "vision": true,
    "audio": true,
    "multimodal": true,
    "tool_calling": true,
    "context_length": 128000,
    "reasoning_level": "high"
  },
  
  "pricing": {
    "input_price_per_1m_tokens": 2.50,
    "output_price_per_1m_tokens": 10.00,
    "currency": "USD"
  },
  
  "scores": {
    "reasoning_score": 92,
    "coding_score": 90,
    "speed_score": 75,
    "cost_efficiency_score": 70,
    "overall_score": 85
  },
  
  "tags": ["multimodal", "reasoning", "coding"],
  
  "source": {
    "model_page": "https://platform.openai.com/docs/models/gpt-4o",
    "api_docs": "https://platform.openai.com/docs/api-reference",
    "pricing_page": "https://openai.com/pricing",
    "last_updated": "2026-04-25"
  }
}
```

### 阶段3: 爬虫重构

1. **更新爬虫基类**

   * 支持新数据结构

   * 添加评分数据获取方法

   * 添加标签生成逻辑

2. **更新厂商爬虫**

   * OpenAI: 添加release\_date、status、scores

   * Anthropic: 添加完整字段

   * Aliyun: 价格单位改为per 1M tokens

3. **新增成本计算模块**

   * 根据输入token数计算总成本

   * 支持对比多个模型的成本

   * 支持场景化估算（聊天、批量处理等）

### 阶段4: API重构

**新API接口**：

| 方法   | 路径                      | 功能         | 参数                                                                |
| ---- | ----------------------- | ---------- | ----------------------------------------------------------------- |
| GET  | /api/models             | 模型列表（增强筛选） | provider, status, tags, min\_context, max\_input\_price, sort\_by |
| GET  | /api/models/{model\_id} | 模型详情       | -                                                                 |
| GET  | /api/providers          | 厂商列表       | -                                                                 |
| GET  | /api/compare            | 模型对比       | models, metrics                                                   |
| POST | /api/cost/calculate     | 成本计算       | model\_id, input\_tokens, output\_tokens                          |
| POST | /api/cost/compare       | 成本对比       | models, input\_tokens, output\_tokens                             |
| GET  | /api/search             | 按标签/能力搜索   | tags, capabilities                                                |
| GET  | /api/status             | 系统状态       | -                                                                 |

### 阶段5: 数据迁移

1. **迁移现有数据**

   * 读取现有models.json

   * 转换为新格式

   * 插入Turso数据库

   * 补充缺失字段（release\_date, scores, tags）

2. **验证数据完整性**

   * 检查所有必填字段

   * 验证价格数据

   * 确认评分合理性

### 阶段6: 测试与部署

1. **本地测试**

   * 测试所有API端点

   * 测试筛选排序

   * 测试成本计算

   * 测试数据更新

2. **Vercel部署**

   * 配置Turso环境变量

   * 部署到Vercel

   * 验证线上功能

3. **GitHub Actions**

   * 更新爬虫脚本使用Turso

   * 测试定时任务

***

## 环境配置

### 环境变量（Vercel）

```
TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your-token
```

### 本地开发

```bash
# 设置环境变量
export TURSO_DATABASE_URL="libsql://your-db.turso.io"
export TURSO_AUTH_TOKEN="your-token"

# 运行
uvicorn api.main:app --reload
```

***

## 时间表（参考）

| 阶段  | 内容     | 复杂度 |
| --- | ------ | --- |
| 阶段1 | 数据库设置  | 低   |
| 阶段2 | 数据结构重构 | 中   |
| 阶段3 | 爬虫重构   | 中   |
| 阶段4 | API重构  | 中高  |
| 阶段5 | 数据迁移   | 中   |
| 阶段6 | 测试部署   | 低   |

***

## 风险与缓解

| 风险             | 影响   | 缓解措施         |
| -------------- | ---- | ------------ |
| Turso注册/配置问题   | 阻塞   | 准备JSON文件备选方案 |
| 爬虫仍被403        | 数据不全 | 使用官方API+手动维护 |
| 数据结构迁移丢失       | 数据丢失 | 先备份，再迁移      |
| Vercel环境变量配置错误 | 线上故障 | 本地充分测试       |

***

## 后续扩展（v0.3.0+）

1. **价格历史追踪**

   * 记录每次价格变动

   * 生成价格趋势图

   * 价格变动告警

2. **用户系统**

   * API Key管理

   * 使用配额控制

   * 用户偏好设置

3. **高级功能**

   * 模型推荐引擎

   * 场景化成本优化

   * 批量导出功能

