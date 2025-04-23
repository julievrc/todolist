from flask import Flask, jsonify, g, request, make_response
import sqlite3
import jwt
from functools import wraps
import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from google.cloud import translate_v2 as translate

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
DATABASE = 'todolist.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    
    db.execute('''
    CREATE TABLE IF NOT EXISTS entries (
        id TEXT PRIMARY KEY,
        what_to_do TEXT NOT NULL,
        due_date TEXT,
        reminder_date TEXT,
        status TEXT DEFAULT 'pending',
        user_id TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    db.commit()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            db = get_db()
            current_user = db.execute('SELECT * FROM users WHERE id = ?', 
                               (data['user_id'],)).fetchone()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    
    user_id = str(uuid.uuid4())
    
    db = get_db()
    try:
        db.execute('INSERT INTO users (id, name, email, password) VALUES (?, ?, ?, ?)',
                  (user_id, data['name'], data['email'], hashed_password))
        db.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'User already exists'}), 409

@app.route('/api/login', methods=['POST'])
def login():
    auth = request.get_json()
    
    if not auth or not auth.get('email') or not auth.get('password'):
        return jsonify({'message': 'Missing email or password'}), 401
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', 
                     (auth['email'],)).fetchone()
    
    if not user or not check_password_hash(user['password'], auth['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }, app.config['SECRET_KEY'])
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email']
        }
    })

@app.route("/api/items")
@token_required
def get_items(current_user):
    db = get_db()
    cur = db.execute('SELECT id, what_to_do, due_date, reminder_date, status FROM entries WHERE user_id = ?',
                    (current_user['id'],))
    entries = cur.fetchall()
    tdlist = [dict(id=row['id'], what_to_do=row['what_to_do'], due_date=row['due_date'], 
                 reminder_date=row['reminder_date'], status=row['status']) for row in entries]
    return jsonify(tdlist)

@app.route("/api/items", methods=['POST'])
@token_required
def add_item(current_user):
    data = request.get_json()
    
    if not data or not data.get('what_to_do'):
        return jsonify({'message': 'Task description is required'}), 400
    
    item_id = str(uuid.uuid4())
    db = get_db()
    db.execute('INSERT INTO entries (id, what_to_do, due_date, reminder_date, status, user_id) VALUES (?, ?, ?, ?, ?, ?)',
              (item_id, data['what_to_do'], data.get('due_date'), data.get('reminder_date'), 'pending', current_user['id']))
    db.commit()
    
    return jsonify({'message': 'Task added successfully', 'id': item_id}), 201

@app.route("/api/items/<item_id>", methods=['PUT'])
@token_required
def update_item(current_user, item_id):
    data = request.get_json()
    
    db = get_db()
    item = db.execute('SELECT * FROM entries WHERE id = ? AND user_id = ?', 
                     (item_id, current_user['id'])).fetchone()
    
    if not item:
        return jsonify({'message': 'Item not found'}), 404
    
    if 'status' in data:
        db.execute('UPDATE entries SET status = ? WHERE id = ?', (data['status'], item_id))
    
    if 'what_to_do' in data:
        db.execute('UPDATE entries SET what_to_do = ? WHERE id = ?', (data['what_to_do'], item_id))
    
    if 'due_date' in data:
        db.execute('UPDATE entries SET due_date = ? WHERE id = ?', (data['due_date'], item_id))
    
    if 'reminder_date' in data:
        db.execute('UPDATE entries SET reminder_date = ? WHERE id = ?', (data['reminder_date'], item_id))
    
    db.commit()
    
    return jsonify({'message': 'Item updated successfully'})

@app.route("/api/items/<item_id>", methods=['DELETE'])
@token_required
def delete_item(current_user, item_id):
    db = get_db()
    item = db.execute('SELECT * FROM entries WHERE id = ? AND user_id = ?', 
                     (item_id, current_user['id'])).fetchone()
    
    if not item:
        return jsonify({'message': 'Item not found'}), 404
    
    db.execute('DELETE FROM entries WHERE id = ?', (item_id,))
    db.commit()
    
    return jsonify({'message': 'Item deleted successfully'})

@app.route("/api/translate", methods=['POST'])
@token_required
def translate_text(current_user):
    data = request.get_json()
    
    if not data or not data.get('text') or not data.get('target_language'):
        return jsonify({'message': 'Text and target language are required'}), 400
    
    try:
        translate_client = translate.Client()
        result = translate_client.translate(
            data['text'],
            target_language=data['target_language']
        )
        
        return jsonify({
            'original_text': data['text'],
            'translated_text': result['translatedText'],
            'source_language': result['detectedSourceLanguage'],
            'target_language': data['target_language']
        })
    except Exception as e:
        return jsonify({'message': f'Translation error: {str(e)}'}), 500

@app.route("/api/user", methods=['GET'])
@token_required
def get_user_profile(current_user):
    return jsonify({
        'id': current_user['id'],
        'name': current_user['name'],
        'email': current_user['email']
    })

# Initialize database when app starts
with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run("0.0.0.0", port=5001)
