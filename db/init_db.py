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
    
    rows = await db.query("SELECT count(*) as cnt FROM models")
    print(f"Current model count: {rows}")
    
    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_database())
