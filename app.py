import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # Max 2MB file

# Make sure images folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('recipes.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            image_filename TEXT,
            author TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Routes ---

@app.route('/')
def home():
    conn = sqlite3.connect('recipes.db')
    c = conn.cursor()
    c.execute('SELECT id, title, description, image_filename FROM recipes')
    recipes = c.fetchall()
    conn.close()
    return render_template('index.html', recipes=recipes)

@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    conn = sqlite3.connect('recipes.db')
    c = conn.cursor()
    c.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,))
    recipe = c.fetchone()
    conn.close()
    return render_template('recipe_detail.html', recipe=recipe)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    conn = sqlite3.connect('recipes.db')
    c = conn.cursor()
    c.execute('SELECT id, title, description, image_filename FROM recipes WHERE title LIKE ?', ('%' + query + '%',))
    recipes = c.fetchall()
    conn.close()
    return render_template('index.html', recipes=recipes, query=query)

@app.route('/add', methods=['GET', 'POST'])
def add_recipe():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        author = request.form['author']
        image = request.files['image']

        if image:
            image_filename = image.filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        else:
            image_filename = None

        conn = sqlite3.connect('recipes.db')
        c = conn.cursor()
        c.execute('INSERT INTO recipes (title, description, image_filename, author) VALUES (?, ?, ?, ?)',
                  (title, description, image_filename, author))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))

    return render_template('add_recipe.html')

if __name__ == "__main__":
    app.run(debug=True)
