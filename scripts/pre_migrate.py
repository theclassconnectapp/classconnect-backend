import asyncio, os, re

async def main():
    url = os.environ.get('DATABASE_URL', '')
    url = re.sub(r'^postgres(ql)?://', 'postgresql://', url)
    
    import asyncpg
    conn = await asyncpg.connect(url)
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """)
        await conn.execute("""
            INSERT INTO alembic_version (version_num) 
            VALUES ('7c0c5985f9c7') 
            ON CONFLICT DO NOTHING
        """)
        print("pre_migrate: done")
    finally:
        await conn.close()

asyncio.run(main())
