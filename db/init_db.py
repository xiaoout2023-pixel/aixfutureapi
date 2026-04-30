import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.turso import TursoDB

async def init_database():
    db = TursoDB()

    print("Testing Turso database connection...")
    try:
        result = await db.execute("SELECT 1 as test")
        print(f"Connection test result: {result}")
    except Exception as e:
        print(f"Connection error: {e}")
        return

    print("Dropping dependent tables first (FK constraints)...")
    await db.execute("DROP TABLE IF EXISTS price_history")
    await db.execute("DROP TABLE IF EXISTS scenario_steps")
    await db.execute("DROP TABLE IF EXISTS scenarios")
    await db.execute("DROP TABLE IF EXISTS leaderboards")
    await db.execute("DROP TABLE IF EXISTS model_marketplace")

    print("Dropping old models table...")
    await db.execute("DROP TABLE IF EXISTS models")

    print("Creating models table (flattened)...")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS models (
            model_id TEXT PRIMARY KEY,
            model_name TEXT NOT NULL,
            provider TEXT NOT NULL,
            release_date TEXT,
            status TEXT DEFAULT 'active',
            last_updated TEXT,
            cap_text INTEGER DEFAULT 1,
            cap_vision INTEGER DEFAULT 0,
            cap_audio INTEGER DEFAULT 0,
            cap_code INTEGER DEFAULT 0,
            cap_reasoning INTEGER DEFAULT 0,
            cap_tool_use INTEGER DEFAULT 0,
            cap_function_calling INTEGER DEFAULT 0,
            cap_image_generation INTEGER DEFAULT 0,
            cap_video_understanding INTEGER DEFAULT 0,
            cap_video_generation INTEGER DEFAULT 0,
            cap_json_mode INTEGER DEFAULT 0,
            cap_structured_output INTEGER DEFAULT 0,
            cap_code_execution INTEGER DEFAULT 0,
            cap_fine_tuning INTEGER DEFAULT 0,
            cap_embedding INTEGER DEFAULT 0,
            context_length INTEGER DEFAULT 0,
            max_output_tokens INTEGER DEFAULT 4096,
            reasoning_level TEXT DEFAULT 'low',
            price_input_per_1m REAL DEFAULT 0,
            price_output_per_1m REAL DEFAULT 0,
            price_cached_input REAL,
            price_batch_input REAL,
            price_batch_output REAL,
            price_per_image REAL,
            price_per_request REAL,
            price_reasoning_per_1m REAL,
            price_currency TEXT DEFAULT 'USD',
            price_free_tier INTEGER DEFAULT 0,
            score_reasoning REAL DEFAULT 0,
            score_coding REAL DEFAULT 0,
            score_speed REAL DEFAULT 0,
            score_cost_efficiency REAL DEFAULT 0,
            score_overall REAL DEFAULT 0,
            score_latency_level TEXT DEFAULT 'medium',
            score_throughput_level TEXT DEFAULT 'medium',
            tags TEXT DEFAULT '[]',
            source_model_page TEXT,
            source_api_docs TEXT,
            source_pricing_page TEXT,
            source_type TEXT DEFAULT 'official',
            source_region_restriction INTEGER DEFAULT 0,
            source_enterprise_only INTEGER DEFAULT 0,
            source_openai_compatible INTEGER DEFAULT 0,
            source_sdk_support INTEGER DEFAULT 0
        )
    """)
    print("Created models table (flattened)")

    print("Creating indexes...")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_models_status ON models(status)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_models_overall ON models(score_overall DESC)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_models_input_price ON models(price_input_per_1m)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_models_output_price ON models(price_output_per_1m)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_models_context ON models(context_length DESC)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_models_vision ON models(cap_vision)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_models_reasoning ON models(cap_reasoning)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_models_reasoning_level ON models(reasoning_level)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_models_free_tier ON models(price_free_tier)")
    print("Created indexes")

    print("Creating price_history table...")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id TEXT NOT NULL,
            input_price REAL,
            output_price REAL,
            recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(model_id) REFERENCES models(model_id)
        )
    """)
    print("Created price_history table")

    print("Creating scenarios table...")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS scenarios (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    print("Created scenarios table")

    print("Creating scenario_steps table...")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS scenario_steps (
            id TEXT PRIMARY KEY,
            scenario_id TEXT NOT NULL,
            step_order INTEGER NOT NULL DEFAULT 0,
            task_type TEXT,
            model_id TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            daily_calls INTEGER DEFAULT 1,
            cache_hit_rate REAL DEFAULT 0.0,
            FOREIGN KEY(scenario_id) REFERENCES scenarios(id),
            FOREIGN KEY(model_id) REFERENCES models(model_id)
        )
    """)
    print("Created scenario_steps table")

    print("Creating leaderboards table...")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS leaderboards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            rank INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            organization TEXT NOT NULL,
            score REAL,
            score_details TEXT,
            is_opensource INTEGER DEFAULT 0,
            is_domestic INTEGER DEFAULT 1,
            release_date TEXT,
            usage_type TEXT DEFAULT 'api',
            is_reasoning INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(category, model_name)
        )
    """)
    print("Created leaderboards table")

    print("Creating model_marketplace table...")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS model_marketplace (
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
        )
    """)
    print("Created model_marketplace table")

    rows = await db.query("SELECT count(*) as cnt FROM models")
    print(f"Current model count: {rows}")

    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_database())
