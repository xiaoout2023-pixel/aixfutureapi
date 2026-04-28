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
    
    print("Creating leaderboard table...")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id TEXT NOT NULL,
            model_name TEXT NOT NULL,
            provider TEXT NOT NULL,
            board_type TEXT NOT NULL,
            parent_board_type TEXT,
            rank INTEGER,
            score REAL,
            sub_scores TEXT,
            generation_time REAL,
            input_price REAL,
            output_price REAL,
            composite_price REAL,
            is_reference INTEGER DEFAULT 0,
            period TEXT,
            source TEXT DEFAULT 'SuperCLUE',
            last_updated TEXT,
            UNIQUE(model_id, board_type, period)
        )
    """)
    print("Created leaderboard table")
    
    try:
        await db.execute("ALTER TABLE leaderboard ADD COLUMN parent_board_type TEXT")
        print("Added parent_board_type column")
    except Exception:
        print("parent_board_type column may already exist, skipping")
    
    rows = await db.query("SELECT count(*) as cnt FROM models")
    print(f"Current model count: {rows}")
    
    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_database())
