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
    
    print("Creating models table...")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS models (
            model_id TEXT PRIMARY KEY,
            model_name TEXT NOT NULL,
            provider TEXT NOT NULL,
            release_date TEXT,
            status TEXT DEFAULT 'active',
            capabilities TEXT,
            pricing TEXT,
            scores TEXT,
            tags TEXT,
            source TEXT,
            last_updated TEXT
        )
    """)
    print("Created models table")
    
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
