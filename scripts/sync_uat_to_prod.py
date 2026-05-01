import asyncio
import httpx
import sys
import os

sys.stdout.reconfigure(line_buffering=True)

UAT_URL = os.environ["UAT_DB_URL"]
UAT_TOKEN = os.environ["UAT_DB_TOKEN"]
PROD_URL = os.environ["PROD_DB_URL"]
PROD_TOKEN = os.environ["PROD_DB_TOKEN"]


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
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
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
        data = resp.json()
        results = data.get("results", [])
        if results and results[0].get("type") == "error":
            raise Exception(f"SQL Error: {results[0]['error']}")
        return data


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


async def get_all_tables(url, token):
    tables = await query_all(url, token, "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    return [t["name"] for t in tables]


async def get_create_sql(url, token, table_name):
    rows = await query_all(url, token, f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if rows:
        return rows[0].get("sql")
    return None


async def drop_all_tables(url, token):
    tables = await get_all_tables(url, token)
    for t in tables:
        print(f"  Dropping: {t}", flush=True)
        await execute_sql(url, token, f"DROP TABLE IF EXISTS {t}")


async def copy_table(source_url, source_token, target_url, target_token, table_name):
    print(f"  Copying: {table_name}", flush=True)

    create_sql = await get_create_sql(source_url, source_token, table_name)
    if not create_sql:
        print(f"    SKIP: No schema for {table_name}", flush=True)
        return 0

    await execute_sql(target_url, target_token, create_sql)

    rows = await query_all(source_url, source_token, f"SELECT * FROM {table_name}")
    if not rows:
        print(f"    Empty table", flush=True)
        return 0

    cols = list(rows[0].keys())
    col_str = ", ".join(cols)
    placeholder_str = ", ".join(["?"] * len(cols))

    total = 0
    for row in rows:
        values = [row.get(col) for col in cols]
        try:
            await execute_sql(target_url, target_token,
                              f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholder_str})", values)
            total += 1
        except Exception as e:
            print(f"    Row error: {e}", flush=True)

    print(f"    {total}/{len(rows)} rows", flush=True)
    return total


async def main():
    print("=" * 60, flush=True)
    print("SYNC: UAT -> PROD Database", flush=True)
    print("=" * 60, flush=True)

    print("\nStep 1: Drop all PROD tables...", flush=True)
    await drop_all_tables(PROD_URL, PROD_TOKEN)

    print("\nStep 2: Copy tables from UAT...", flush=True)
    source_tables = await get_all_tables(UAT_URL, UAT_TOKEN)
    print(f"UAT tables: {source_tables}", flush=True)

    total_rows = 0
    for table in source_tables:
        count = await copy_table(UAT_URL, UAT_TOKEN, PROD_URL, PROD_TOKEN, table)
        total_rows += count

    print(f"\nTotal rows synced: {total_rows}", flush=True)

    print("\nStep 3: Verify PROD...", flush=True)
    for table in source_tables:
        try:
            rows = await query_all(PROD_URL, PROD_TOKEN, f"SELECT COUNT(*) as cnt FROM {table}")
            cnt = rows[0]["cnt"] if rows else 0
            print(f"  {table}: {cnt} rows", flush=True)
        except Exception as e:
            print(f"  {table}: ERROR - {e}", flush=True)

    print("\nSYNC COMPLETE!", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
