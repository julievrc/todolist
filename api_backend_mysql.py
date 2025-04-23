from flask import Flask, jsonify, g, request, make_response
import pymysql
import jwt
from functools import wraps
import datetime
import os
import requests
import json
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'mysql')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'todouser')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', 'todopassword')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'tododb')

def get_db():
    """Connect to the MySQL database."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            cursorclass=pymysql.cursors.DictCursor
        )
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database tables if they don't exist."""
    db = get_db()
    cursor = db.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id VARCHAR(36) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create entries table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entries (
        id VARCHAR(36) PRIMARY KEY,
        what_to_do TEXT NOT NULL,
        due_date DATETIME,
        reminder_date DATETIME,
        status VARCHAR(20) DEFAULT 'pending',
        user_id VARCHAR(36),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    db.commit()

def token_required(f):
    """Decorator to require a valid JWT token for API access."""
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
            cursor = db.cursor()
            cursor.execute('SELECT * FROM users WHERE id = %s', (data['user_id'],))
            current_user = cursor.fetchone()
            
            if not current_user:
                raise Exception('User not found')
                
        except Exception as e:
            return jsonify({'message': f'Token is invalid! {str(e)}'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    user_id = str(uuid.uuid4())
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO users (id, name, email, password) VALUES (%s, %s, %s, %s)',
            (user_id, data['name'], data['email'], hashed_password)
        )
        db.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except pymysql.err.IntegrityError:
        return jsonify({'message': 'User already exists'}), 409

@app.route('/api/login', methods=['POST'])
def login():
    """Login a user and return a JWT token."""
    auth = request.get_json()
    
    if not auth or not auth.get('email') or not auth.get('password'):
        return jsonify({'message': 'Missing email or password'}), 401
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE email = %s', (auth['email'],))
    user = cursor.fetchone()
    
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
    """Get all todo items for the current user."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'SELECT id, what_to_do, due_date, reminder_date, status FROM entries WHERE user_id = %s',
        (current_user['id'],)
    )
    entries = cursor.fetchall()
    
    # Format dates for JSON serialization
    for entry in entries:
        if entry['due_date']:
            entry['due_date'] = entry['due_date'].strftime('%Y-%m-%d %H:%M:%S')
        if entry['reminder_date']:
            entry['reminder_date'] = entry['reminder_date'].strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify(entries)

@app.route("/api/items", methods=['POST'])
@token_required
def add_item(current_user):
    """Add a new todo item."""
    data = request.get_json()
    
    if not data or not data.get('what_to_do'):
        return jsonify({'message': 'Task description is required'}), 400
    
    item_id = str(uuid.uuid4())
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute(
        'INSERT INTO entries (id, what_to_do, due_date, reminder_date, status, user_id) VALUES (%s, %s, %s, %s, %s, %s)',
        (
            item_id,
            data['what_to_do'],
            data.get('due_date'),
            data.get('reminder_date'),
            'pending',
            current_user['id']
        )
    )
    db.commit()
    
    return jsonify({'message': 'Task added successfully', 'id': item_id}), 201

@app.route("/api/items/<item_id>", methods=['PUT'])
@token_required
def update_item(current_user, item_id):
    """Update an existing todo item."""
    data = request.get_json()
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'SELECT * FROM entries WHERE id = %s AND user_id = %s',
        (item_id, current_user['id'])
    )
    item = cursor.fetchone()
    
    if not item:
        return jsonify({'message': 'Item not found'}), 404
    
    update_fields = []
    params = []
    
    if 'status' in data:
        update_fields.append('status = %s')
        params.append(data['status'])
    
    if 'what_to_do' in data:
        update_fields.append('what_to_do = %s')
        params.append(data['what_to_do'])
    
    if 'due_date' in data:
        update_fields.append('due_date = %s')
        params.append(data['due_date'])
    
    if 'reminder_date' in data:
        update_fields.append('reminder_date = %s')
        params.append(data['reminder_date'])
    
    if update_fields:
        query = f"UPDATE entries SET {', '.join(update_fields)} WHERE id = %s"
        params.append(item_id)
        cursor.execute(query, params)
        db.commit()
    
    return jsonify({'message': 'Item updated successfully'})

@app.route("/api/items/<item_id>", methods=['DELETE'])
@token_required
def delete_item(current_user, item_id):
    """Delete a todo item."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'SELECT * FROM entries WHERE id = %s AND user_id = %s',
        (item_id, current_user['id'])
    )
    item = cursor.fetchone()
    
    if not item:
        return jsonify({'message': 'Item not found'}), 404
    
    cursor.execute('DELETE FROM entries WHERE id = %s', (item_id,))
    db.commit()
    
    return jsonify({'message': 'Item deleted successfully'})

@app.route("/api/translate", methods=['POST'])
@token_required
def translate_text(current_user):
    """Translate text using public translation APIs."""
    data = request.get_json()
    
    if not data or not data.get('text') or not data.get('target_language'):
        return jsonify({'message': 'Text and target language are required'}), 400
    
    original_text = data['text']
    target_lang = data['target_language']
    
    print(f"Translating: '{original_text}' to {target_lang}")
    
    # Ensure we're using standard language codes for all APIs
    # MyMemory API language codes
    mymemory_lang_map = {
        'en': 'en',
        'fr': 'fr',
        'es': 'es', 
        'it': 'it',
        'de': 'de',
        'zh-CN': 'zh',  # MyMemory uses 'zh' for Chinese
        'ja': 'ja',
        'ko': 'ko',
        'ru': 'ru'
    }
    
    # Google Translate language codes
    google_lang_map = {
        'en': 'en',
        'fr': 'fr',
        'es': 'es',
        'it': 'it',
        'de': 'de',
        'zh-CN': 'zh',  # Google sometimes uses just 'zh'
        'ja': 'ja',
        'ko': 'ko',
        'ru': 'ru'
    }
    
    # LingoJAM language codes
    lingo_lang_map = {
        'en': 'english',
        'fr': 'french',
        'es': 'spanish',
        'it': 'italian',
        'de': 'german',
        'zh-CN': 'chinese',
        'ja': 'japanese',
        'ko': 'korean',
        'ru': 'russian'
    }
    
    # Import urllib.parse for URL encoding
    import urllib.parse
    encoded_text = urllib.parse.quote(original_text)
    
    # 1. First attempt: MyMemory Translation API
    try:
        mm_lang = mymemory_lang_map.get(target_lang, target_lang)
        url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair=en|{mm_lang}"
        
        print(f"Trying MyMemory API: {url}")
        response = requests.get(url)
        
        if response.status_code == 200:
            result = response.json()
            
            if result and 'responseData' in result and 'translatedText' in result['responseData']:
                translated_text = result['responseData']['translatedText']
                
                # Sometimes the API returns HTML entities, let's fix that
                import html
                translated_text = html.unescape(translated_text)
                
                # Check if we got a sensible translation (not just the original text)
                if translated_text.lower() != original_text.lower():
                    return jsonify({
                        'original_text': original_text,
                        'translated_text': translated_text,
                        'source_language': 'en',
                        'target_language': target_lang,
                        'service': 'MyMemory Translation API'
                    })
    except Exception as e:
        print(f"MyMemory API exception: {str(e)}")
    
    # 2. Direct method for Asian languages and Russian
    if target_lang in ['zh-CN', 'ja', 'ko', 'ru']:
        try:
            # Use a different approach for these languages
            # This approach works very well for Asian languages and Russian
            target = target_lang.split('-')[0] if '-' in target_lang else target_lang
            
            # Using a simpler URL format that works well with these languages
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target}&dt=t&q={encoded_text}"
            
            print(f"Trying specialized API for {target_lang}: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                try:
                    # Parse the response
                    content = response.text
                    
                    # Sometimes the response might not be valid JSON, so we'll parse it carefully
                    import json
                    result = json.loads(content)
                    
                    if result and isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
                        # Extract the translation from Google's nested array format
                        translated_parts = []
                        for item in result[0]:
                            if item and len(item) > 0 and isinstance(item[0], str):
                                translated_parts.append(item[0])
                        
                        translated_text = ''.join(translated_parts)
                        
                        # If we got a valid translation, return it
                        if translated_text and translated_text.strip():
                            return jsonify({
                                'original_text': original_text,
                                'translated_text': translated_text,
                                'source_language': 'en',
                                'target_language': target_lang,
                                'service': 'Google Translate (Specialized)'
                            })
                except Exception as e:
                    print(f"Specialized translation parsing error: {str(e)}")
        except Exception as e:
            print(f"Specialized translation API exception: {str(e)}")
    
    # 3. General Google Translate API (unofficial)
    try:
        google_lang = google_lang_map.get(target_lang, target_lang)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={google_lang}&dt=t&q={encoded_text}"
        
        print(f"Trying Google Translate API: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result and isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
                    # Extract the translation from Google's nested array format
                    translated_parts = [part[0] for part in result[0] if part and len(part) > 0]
                    translated_text = ''.join(translated_parts)
                    
                    # Check if we got a sensible translation
                    if translated_text.lower() != original_text.lower():
                        return jsonify({
                            'original_text': original_text,
                            'translated_text': translated_text,
                            'source_language': 'auto',
                            'target_language': target_lang,
                            'service': 'Google Translate'
                        })
            except Exception as e:
                print(f"Google Translate parsing error: {str(e)}")
    except Exception as e:
        print(f"Google Translate API exception: {str(e)}")
    
    # 3. Third attempt: LingoJAM API
    try:
        if target_lang in lingo_lang_map:
            lingo_lang = lingo_lang_map[target_lang]
            
            url = f"https://lingojam.com/api/api.php?action=translate&from=english&to={lingo_lang}&text={encoded_text}"
            print(f"Trying LingoJAM API: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result and 'translatedText' in result:
                    translated_text = result['translatedText']
                    
                    # Check if we got a sensible translation
                    if translated_text.lower() != original_text.lower():
                        return jsonify({
                            'original_text': original_text,
                            'translated_text': translated_text,
                            'source_language': 'en',
                            'target_language': target_lang,
                            'service': 'LingoJAM Translation'
                        })
    except Exception as e:
        print(f"LingoJAM API exception: {str(e)}")
    
    # 4. Fourth attempt: LibreTranslate API
    try:
        url = "https://libretranslate.com/translate"
        payload = {
            "q": original_text,
            "source": "en",
            "target": target_lang,
            "format": "text",
            "api_key": ""  # LibreTranslate may require an API key for some instances
        }
        
        print(f"Trying LibreTranslate API")
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if 'translatedText' in result:
                translated_text = result['translatedText']
                
                # Check if we got a sensible translation
                if translated_text.lower() != original_text.lower():
                    return jsonify({
                        'original_text': original_text,
                        'translated_text': translated_text,
                        'source_language': 'en',
                        'target_language': target_lang,
                        'service': 'LibreTranslate'
                    })
    except Exception as e:
        print(f"LibreTranslate API exception: {str(e)}")
    
    # Special handling for Asian languages and Russian as final attempt
    if target_lang in ['zh-CN', 'ja', 'ko', 'ru']:
        try:
            # Target language code processing
            if target_lang == 'zh-CN':
                target_code = 'zh'
            else:
                target_code = target_lang
                
            # Using yet another endpoint that's particularly good for these languages
            url = f"https://translation.googleapis.com/language/translate/v2?key=&q={encoded_text}&source=en&target={target_code}"
            
            print(f"Trying final specialized endpoint for {target_lang}: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://translate.google.com/',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            content = response.text
            
            # Parse the response - handle it carefully as it may not be JSON
            try:
                if "data" in content:
                    import re
                    # Try to extract the translation using regex for reliability
                    match = re.search(r'"translatedText":\s*"([^"]+)"', content)
                    if match:
                        translated_text = match.group(1)
                        
                        # Fix any escaped characters
                        import html
                        translated_text = html.unescape(translated_text)
                        
                        if translated_text and translated_text.strip():
                            return jsonify({
                                'original_text': original_text,
                                'translated_text': translated_text,
                                'source_language': 'en',
                                'target_language': target_lang,
                                'service': 'Google Cloud Translation API (Special)'
                            })
            except Exception as e:
                print(f"Special endpoint parsing error: {str(e)}")
        except Exception as e:
            print(f"Special endpoint exception: {str(e)}")
    
    # Final general attempt: another fallback method
    try:
        # Constructing a backup URL for translation
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Using another approach for Google Translate
        url = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=en&tl={target_lang}&q={encoded_text}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            try:
                # This API has a different response format
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    translated_text = result[0]
                    
                    # Check if we got a sensible translation
                    if translated_text.lower() != original_text.lower():
                        return jsonify({
                            'original_text': original_text,
                            'translated_text': translated_text,
                            'source_language': 'en',
                            'target_language': target_lang,
                            'service': 'Google Translate (Alternative)'
                        })
            except Exception as e:
                print(f"Alternative parsing error: {str(e)}")
    except Exception as e:
        print(f"Final fallback exception: {str(e)}")
    
    # If all translation services fail, we return the original text
    print("All translation APIs failed")
    return jsonify({
        'original_text': original_text,
        'translated_text': original_text,  # Return original if all APIs fail
        'source_language': 'en',
        'target_language': target_lang,
        'service': 'No translation available'
    })

def advanced_word_translation(text, target_lang):
    """This function is kept as a stub for backward compatibility."""
    # Since some existing code might call this function, we keep it as a stub
    # that simply returns the original text
    return text

@app.route("/api/user", methods=['GET'])
@token_required
def get_user_profile(current_user):
    """Get the current user's profile information."""
    return jsonify({
        'id': current_user['id'],
        'name': current_user['name'],
        'email': current_user['email']
    })

@app.route("/health")
def health_check():
    """Health check endpoint for Kubernetes liveness probe."""
    try:
        # Test database connection
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT 1')
        return jsonify({"status": "healthy", "db_connection": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# Initialize database when app starts
with app.app_context():
    try:
        init_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    app.run("0.0.0.0", port=5001)