import asyncio
import httpx
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SOURCE_URL = "libsql://modelstemp2-xiaoout.aws-us-west-2.turso.io"
SOURCE_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Nzc0MTI2OTcsImlkIjoiMDE5ZGQ2MGQtNDUwMS03YTA0LWEwMzYtOTM2MzJiMGI1MDJlIiwicmlkIjoiYjYxZGM1MzEtYWZhNi00ODQzLTlkMTYtNjhkYTY3ZGY1MTdjIn0.HV3mUz8GH3BJ2lOGJvCnuQF0xqiPwIwLTq5DaAtKfOLzwqL6iLNZj8XCnEA8sbaN2mzpxvRUc7rLB9quqCIbCw"

TARGETS = [
    {
        "name": "ai-models-db-xiaoout (UAT)",
        "url": "libsql://ai-models-db-xiaoout.aws-us-west-2.turso.io",
        "token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NzcxMzk0NTcsImlkIjoiMDE5ZGM1YzMtYjEwMS03ZmI3LTk2MTktMjcxMTQ5MTc0NjMxIiwicmlkIjoiMWRiYjJmYmQtYzBiOS00MGVmLTk1OGYtODMxMDQ5OGI3MGEwIn0.ZJPCre8vUElMfKyEJITI6cdLcj9yDwjGxd49FmoXYBe5VlaVbs4LTKYffeTzbbKZGYOB8KCd-ubqrzjOs6mGCg",
    },
    {
        "name": "aixfutureprod-xiaoout (PROD)",
        "url": "libsql://aixfutureprod-xiaoout.aws-us-west-2.turso.io",
        "token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Nzc0MTEwNjMsImlkIjoiMDE5ZGQ1ZjItZWQwMS03MjIxLWExYTAtODkxYjYzMTE2MWI2IiwicmlkIjoiNGQxMWU5MGEtNzE2NC00MjIzLWE0OGMtNGVjYWQ0NjAzOWM4In0.tJJcjMjfiAewjYpblXM8S1NKcSDZT0UBsBSmwYXz7DsU6I3kQXlyVvyAI8-sgKsGE4y6LZpbIw2viWg70tkhDQ",
    },
]

TABLES_TO_COPY = ["models", "model_marketplace", "price_history", "scenarios", "scenario_steps", "leaderboards"]


def _url_to_http(url):
    return url.replace("libsql://", "https://")


def _format_args(params):
    if not params:
        return None
    args = []
    for p in params:
        if p is None:
            args.append({"type": "null"})
        elif isinstance(p, bool):
            args.append({"type": "text", "value": "1" if p else "0"})
        elif isinstance(p, float):
            args.append({"type": "text", "value": str(p)})
        elif isinstance(p, int):
            args.append({"type": "integer", "value": str(p)})
        else:
            args.append({"type": "text", "value": str(p)})
    return args


async def execute_sql(url, token, sql, params=None):
    http_url = _url_to_http(url)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    stmt = {"sql": sql}
    formatted_args = _format_args(params)
    if formatted_args:
        stmt["args"] = formatted_args
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{http_url}/v2/pipeline",
            json={"requests": [{"type": "execute", "stmt": stmt}]},
            headers=headers
        )
        resp.raise_for_status()
        return resp.json()


async def execute_batch(url, token, statements):
    http_url = _url_to_http(url)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    requests = []
    for sql, params in statements:
        stmt = {"sql": sql}
        formatted_args = _format_args(params)
        if formatted_args:
            stmt["args"] = formatted_args
        requests.append({"type": "execute", "stmt": stmt})
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{http_url}/v2/pipeline",
            json={"requests": requests},
            headers=headers
        )
        resp.raise_for_status()
        return resp.json()


async def query_all(url, token, sql, params=None):
    result = await execute_sql(url, token, sql, params)
    results = result.get("results", [])
    if not results:
        return []
    result_data = results[0].get("response", {}).get("result", {})
    if not result_data:
        return []
    cols = [c.get("name", "") for c in result_data.get("cols", [])]
    rows = []
    for row in result_data.get("rows", []):
        converted = {}
        for i, col in enumerate(cols):
            val = row[i]
            if isinstance(val, dict):
                if val.get("type") == "null":
                    converted[col] = None
                elif "value" in val:
                    converted[col] = val["value"]
                else:
                    converted[col] = None
            else:
                converted[col] = val
        rows.append(converted)
    return rows


async def get_table_info(url, token):
    tables = await query_all(url, token, "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [t["name"] for t in tables]


async def get_create_table_sql(url, token, table_name):
    rows = await query_all(url, token, f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if rows:
        return rows[0].get("sql")
    return None


async def copy_table(source_url, source_token, target_url, target_token, table_name):
    print(f"  Copying table: {table_name}")

    create_sql = await get_create_table_sql(source_url, source_token, table_name)
    if not create_sql:
        print(f"    SKIP: No CREATE TABLE SQL found for {table_name}")
        return 0

    try:
        await execute_sql(target_url, target_token, f"DROP TABLE IF EXISTS {table_name}")
    except Exception as e:
        print(f"    Warning: DROP TABLE failed: {e}")

    try:
        await execute_sql(target_url, target_token, create_sql)
    except Exception as e:
        print(f"    Warning: CREATE TABLE failed (may already exist): {e}")

    rows = await query_all(source_url, source_token, f"SELECT * FROM {table_name}")
    if not rows:
        print(f"    No data in {table_name}")
        return 0

    cols = list(rows[0].keys())
    col_str = ", ".join(cols)
    placeholder_str = ", ".join(["?"] * len(cols))

    batch_size = 20
    total_copied = 0

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        statements = []
        for row in batch:
            values = [row.get(col) for col in cols]
            sql = f"INSERT OR REPLACE INTO {table_name} ({col_str}) VALUES ({placeholder_str})"
            statements.append((sql, values))

        try:
            await execute_batch(target_url, target_token, statements)
            total_copied += len(batch)
        except Exception as e:
            print(f"    Error inserting batch {i//batch_size}: {e}")
            for row in batch:
                values = [row.get(col) for col in cols]
                try:
                    await execute_sql(target_url, target_token,
                                      f"INSERT OR REPLACE INTO {table_name} ({col_str}) VALUES ({placeholder_str})",
                                      values)
                    total_copied += 1
                except Exception as e2:
                    print(f"      Failed row: {e2}")

    print(f"    Copied {total_copied}/{len(rows)} rows")
    return total_copied


async def main():
    print("=" * 60)
    print("Database Copy: modelstemp2-xiaoout -> targets")
    print("=" * 60)

    source_tables = await get_table_info(SOURCE_URL, SOURCE_TOKEN)
    print(f"\nSource tables: {source_tables}")

    for target in TARGETS:
        print(f"\n{'=' * 60}")
        print(f"Target: {target['name']}")
        print(f"URL: {target['url']}")
        print(f"{'=' * 60}")

        target_tables = await get_table_info(target["url"], target["token"])
        print(f"Existing target tables: {target_tables}")

        total_rows = 0
        for table in TABLES_TO_COPY:
            if table in source_tables:
                count = await copy_table(SOURCE_URL, SOURCE_TOKEN, target["url"], target["token"], table)
                total_rows += count
            else:
                print(f"  SKIP: {table} not found in source")

        print(f"\nTotal rows copied to {target['name']}: {total_rows}")

        print(f"\nVerifying {target['name']}...")
        for table in TABLES_TO_COPY:
            try:
                rows = await query_all(target["url"], target["token"], f"SELECT COUNT(*) as cnt FROM {table}")
                cnt = rows[0]["cnt"] if rows else 0
                print(f"  {table}: {cnt} rows")
            except Exception as e:
                print(f"  {table}: ERROR - {e}")

    print("\n" + "=" * 60)
    print("Database copy completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
