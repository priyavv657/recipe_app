import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def get_db_connection():
    conn = sqlite3.connect('cookbook.db')
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    if user:
        session['username'] = username
        return redirect(url_for('dashboard'))
    return "Invalid credentials", 403

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        conn.close()
        return "User already exists", 400
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()
    session['username'] = username
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))

    query = request.args.get('search', '').lower()
    conn = get_db_connection()
    if query:
        recipes = conn.execute("SELECT * FROM recipes WHERE LOWER(title) LIKE ?", ('%' + query + '%',)).fetchall()
    else:
        recipes = conn.execute("SELECT * FROM recipes").fetchall()
    conn.close()
    return render_template('dashboard.html', recipes=recipes, search=query, show_saved=False)

@app.route('/add', methods=['POST'])
def add_recipe():
    if 'username' not in session:
        return redirect(url_for('home'))

    title = request.form['title']
    author = request.form['author']
    instructions = request.form['content']
    image_file = request.files.get('image_file')
    image_path = ''

    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)
        image_path = '/' + image_path

    conn = get_db_connection()
    conn.execute("INSERT INTO recipes (title, author, image, instructions) VALUES (?, ?, ?, ?)",
                 (title, author, image_path, instructions))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    conn = get_db_connection()
    recipe = conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    conn.close()
    if recipe is None:
        return "Recipe not found", 404
    return render_template('recipe.html', recipe=recipe)

@app.route('/save_recipe/<int:recipe_id>')
def save_recipe(recipe_id):
    if 'username' not in session:
        return redirect(url_for('home'))

    conn = get_db_connection()
    user = conn.execute('SELECT id FROM users WHERE username = ?', (session['username'],)).fetchone()
    if user:
        user_id = user['id']
        already_saved = conn.execute("SELECT * FROM saved_recipes WHERE user_id = ? AND recipe_id = ?", (user_id, recipe_id)).fetchone()
        if not already_saved:
            conn.execute("INSERT INTO saved_recipes (user_id, recipe_id) VALUES (?, ?)", (user_id, recipe_id))
            conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/saved')
def view_saved():
    if 'username' not in session:
        return redirect(url_for('home'))

    conn = get_db_connection()
    user = conn.execute('SELECT id FROM users WHERE username = ?', (session['username'],)).fetchone()
    saved = conn.execute(
        'SELECT recipes.* FROM recipes JOIN saved_recipes ON recipes.id = saved_recipes.recipe_id WHERE saved_recipes.user_id = ?',
        (user['id'],)
    ).fetchall()
    conn.close()
    return render_template('dashboard.html', recipes=saved, search="Saved Recipes", show_saved=True)

@app.route('/delete_recipe/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    if 'username' not in session:
        return redirect(url_for('home'))

    conn = get_db_connection()
    recipe = conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()

    if recipe and recipe['author'] == session['username']:
        conn.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.execute("DELETE FROM saved_recipes WHERE recipe_id = ?", (recipe_id,))
        conn.commit()
    
    conn.close()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
