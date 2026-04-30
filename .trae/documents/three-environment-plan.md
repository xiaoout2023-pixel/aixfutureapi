# 三环境分离方案

## 问题背景
当前只有一个 Turso 数据库 `ai-models-db-xiaoout`，已被新的平铺表结构覆盖。生产环境（main 分支 + aixfutrueapi.top）使用的是旧的 JSON 嵌套结构代码，但数据库已变成新结构，导致生产环境崩溃。

## 目标环境架构

| 环境 | 分支 | 数据库 | Vercel URL | 本地端口 |
|------|------|--------|------------|----------|
| 开发(dev) | master | ai-models-db-dev (新建) | - | 8081 |
| UAT | master | ai-models-db-xiaoout (当前) | aixfutureapi.vercel.app | - |
| 生产(prod) | main | ai-models-db-prod (PITR恢复) | aixfutrueapi.top | - |

## 执行步骤

### 第一步：恢复生产数据库（最紧急）

**方案：使用 Turso PITR（时间点恢复）创建生产数据库**

需要确定的时间点：在我们执行 `DROP TABLE models` 之前。根据 git log，最后一次正常运行的 commit 是 `83c5490`（main 分支），数据库被破坏是在本次会话中执行 `rebuild_db.py` 时发生的。

**操作方式**（需要人工执行，因为需要 Turso Platform API Token）：

1. 安装 Turso CLI：`brew install tursodatabase/tap/turso` 或 `irm https://get.tur.so/install.sh | iex`
2. 登录：`turso auth login`
3. 查看当前数据库列表：`turso db list`
4. 使用 PITR 创建生产数据库：
   ```bash
   turso db create ai-models-db-prod --group default --from-db ai-models-db-xiaoout --timestamp "2026-04-29T00:00:00Z"
   ```
   （时间戳需要在 DROP TABLE 操作之前，可能需要调整）
5. 为新数据库创建 token：
   ```bash
   turso db tokens create ai-models-db-prod
   ```
6. 记录新数据库的连接 URL 和 token

**如果 PITR 不可用（免费用户限制 24 小时）的备选方案**：
- 在当前数据库上重建旧表结构，重新运行旧版爬虫填充数据
- 需要切换到 main 分支代码，运行 `python -m db.init_db` + `python -m crawler.run_all`

### 第二步：创建开发数据库

1. 从当前数据库创建分支作为开发库：
   ```bash
   turso db create ai-models-db-dev --group default --from-db ai-models-db-xiaoout
   ```
2. 为新数据库创建 token：
   ```bash
   turso db tokens create ai-models-db-dev
   ```

### 第三步：修改代码支持多环境

修改 `db/turso.py`，根据环境变量选择不同的数据库：

```python
import os

ENV = os.environ.get("APP_ENV", "dev")

DB_CONFIG = {
    "dev": {
        "url": os.environ.get("TURSO_DEV_URL", "libsql://ai-models-db-dev.aws-us-west-2.turso.io"),
        "token": os.environ.get("TURSO_DEV_TOKEN", "")
    },
    "uat": {
        "url": os.environ.get("TURSO_UAT_URL", "libsql://ai-models-db-xiaoout.aws-us-west-2.turso.io"),
        "token": os.environ.get("TURSO_UAT_TOKEN", "")
    },
    "prod": {
        "url": os.environ.get("TURSO_PROD_URL", "libsql://ai-models-db-prod.aws-us-west-2.turso.io"),
        "token": os.environ.get("TURSO_PROD_TOKEN", "")
    }
}
```

### 第四步：配置 Vercel 环境变量

**生产环境 (aixfutrueapi.top → main 分支)**：
- `APP_ENV=prod`
- `TURSO_PROD_URL=libsql://ai-models-db-prod.xxx.turso.io`
- `TURSO_PROD_TOKEN=<prod-token>`
- `TURSO_DATABASE_URL` = 同 `TURSO_PROD_URL`（兼容旧代码）

**UAT 环境 (aixfutureapi.vercel.app → master 分支)**：
- `APP_ENV=uat`
- `TURSO_UAT_URL=libsql://ai-models-db-xiaoout.aws-us-west-2.turso.io`
- `TURSO_UAT_TOKEN=<uat-token>`
- `TURSO_DATABASE_URL` = 同 `TURSO_UAT_URL`（兼容旧代码）

**本地开发 (master 分支，端口 8081)**：
- `.env` 文件中设置 `APP_ENV=dev`
- `TURSO_DEV_URL` / `TURSO_DEV_TOKEN`

### 第五步：Vercel 项目配置

需要确认 Vercel 上的两个项目：
1. **生产项目**：绑定 main 分支，域名 aixfutrueapi.top
2. **UAT 项目**：绑定 master 分支，域名 aixfutureapi.vercel.app

如果当前只有一个 Vercel 项目，需要创建第二个项目或在 Vercel 中配置 Preview Deployments。

### 第六步：本地开发配置

创建 `.env` 文件（加入 .gitignore）：
```
APP_ENV=dev
TURSO_DEV_URL=libsql://ai-models-db-dev.xxx.turso.io
TURSO_DEV_TOKEN=<dev-token>
```

本地启动命令：`python -m uvicorn api.main:app --host 0.0.0.0 --port 8081`

### 第七步：验证

1. 验证生产环境：访问 https://www.aixfutrueapi.top/api/status，确认使用旧结构
2. 验证 UAT 环境：访问 https://aixfutureapi.vercel.app/api/status，确认使用新平铺结构
3. 验证开发环境：本地 curl http://localhost:8081/api/status，确认使用新平铺结构

## 风险与注意事项

1. **PITR 时间窗口**：免费用户只有 24 小时，如果 DROP TABLE 操作超过 24 小时，则无法恢复
2. **Turso 数据库配额**：每个计划有数据库数量限制，3 个数据库可能需要升级计划
3. **API Token 安全**：不要将 token 硬编码在代码中，使用环境变量
4. **数据库 schema 兼容性**：生产环境（main 分支）使用旧 JSON 结构代码，必须连接旧 schema 的数据库
5. **代码兼容性**：main 分支代码需要能正确连接生产数据库，master 分支代码需要能正确连接 UAT/开发数据库

## 需要用户提供的信息

1. Turso 账号的组织 slug（用于 Platform API）
2. Turso Platform API Token（不是数据库 token，是管理 token）
3. 当前 Turso 计划类型（免费/付费，决定 PITR 时间窗口和数据库配额）
4. Vercel 项目配置（是否已有两个项目，还是需要新建）
5. DROP TABLE 操作的大致时间（用于确定 PITR 时间戳）
