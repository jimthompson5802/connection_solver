import asyncio
import aiosqlite

async def async_db_operation(item, db, db_lock):
    async with db_lock:
        await db.execute('INSERT INTO example_table (value) VALUES (?)', (item,))
        await db.commit()
        async with db.execute('SELECT * FROM example_table WHERE value = ?', (item,)) as cursor:
            row = await cursor.fetchone()
            return row

async def main():
    db_lock = asyncio.Lock()
    async with aiosqlite.connect(':memory:') as db:
        await db.execute('CREATE TABLE example_table (id INTEGER PRIMARY KEY, value INTEGER)')
        await db.commit()
        
        items = [1, 2, 3, 4, 5]
        tasks = [async_db_operation(item, db, db_lock) for item in items]
        results = await asyncio.gather(*tasks)
        print(results)

# Run the main function
asyncio.run(main())