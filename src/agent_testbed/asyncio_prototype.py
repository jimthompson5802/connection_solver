import pandas as pd
import numpy as np
import json
import aiosqlite
import asyncio

# Create a sample DataFrame
data = {
    'word': ['Alice', 'Bob', 'Charlie'], 
    'definition': ["this is alice", "this is bob", "this is charlie"],
    # gerate random array of dimension 5
    'embedding': [np.random.rand(5) for _ in range(3)]
    }
df = pd.DataFrame(data)

print(df)

# convert the embedding to string
df['embedding'] = [json.dumps(e.tolist()) for e in df['embedding'].values.tolist()]
print(df.dtypes)
print(df.embedding.values)

async def write_to_db(df, db_path):
    async with aiosqlite.connect(db_path) as db:
        await db.execute('DROP TABLE IF EXISTS vocabulary')
        await db.execute('CREATE TABLE vocabulary (word TEXT, definition TEXT, embedding TEXT)')
        await db.executemany('INSERT INTO vocabulary (word, definition, embedding) VALUES (?, ?, ?)', df.values.tolist())
        await db.commit()

async def read_from_db(db_path, query):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            df = pd.DataFrame(rows, columns=columns)
            return df

async def main():
    db_path = 'example.db'
    await write_to_db(df, db_path)
    query = 'SELECT * FROM vocabulary'
    df_from_db = await read_from_db(db_path, query)
    print(df_from_db)

    print(f"Are the DataFrames equal? {df.equals(df_from_db)}")
    print(f"Are the embeddings equal? {all(df['embedding'] == df_from_db['embedding'])}")
    print(f"values of embedding in df: {df_from_db['embedding'].values}")

# Run the async function
asyncio.run(main())