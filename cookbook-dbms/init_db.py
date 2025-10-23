# init_db.py
import sqlite3

conn = sqlite3.connect('cookbook.db')
c = conn.cursor()

# Users table
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
''')

# Recipes table
c.execute('''
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        image TEXT,
        instructions TEXT NOT NULL
    )
''')

# Saved recipes table
c.execute('''
    CREATE TABLE IF NOT EXISTS saved_recipes (
        user_id INTEGER,
        recipe_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (recipe_id) REFERENCES recipes(id)
    )
''')

conn.commit()
conn.close()
