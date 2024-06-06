from flask import Flask, request, jsonify
import sqlite3
import json
import difflib
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
db_path = 'shona.db'

# Create SQLite database and table
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS shona_words (
    id INTEGER PRIMARY KEY,
    word TEXT,
    meaning_1 TEXT,
    meaning_2 TEXT,
    similar_words TEXT,
    example_sentence TEXT
)''')
conn.commit()
conn.close()

# Load the data from the JSON file
def load_shona(json_file, db_path):
    with open(json_file, 'r', encoding='utf-8') as f:
        shona = json.load(f)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create the table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS shona_words (
        id INTEGER PRIMARY KEY,
        word TEXT,
        meaning_1 TEXT,
        meaning_2 TEXT,
        similar_words TEXT,
        example_sentence TEXT
    )''')
    conn.commit()

    for word_entry in shona['words']:
        word = word_entry['word']
        meaning_1 = word_entry['meaning_1']
        meaning_2 = word_entry.get('meaning_2')
        similar_words = word_entry['similar_words']
        example_sentence = word_entry['example_sentence']

        # Insert the word into the database
        c.execute('INSERT INTO shona_words (word, meaning_1, meaning_2, similar_words, example_sentence) VALUES (?, ?, ?, ?, ?)',
                  (word,meaning_1, meaning_2, similar_words, example_sentence))
        print(f'Added word "{word}" to the database')

    conn.commit()
    conn.close()

@app.route('/', methods=['POST'])
def add_word():
    return jsonify({'message': 'Welcome to module 2'})

@app.route('/add_word', methods=['POST'])
def add_word():
    word_data = request.json
    if not word_data:
        return jsonify({'message': 'No data provided'})

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT * FROM shona_words WHERE word=?', (word_data['word'],))
    existing_word = c.fetchone()

    if existing_word:
        conn.close()
        return jsonify({'message': 'Word already exists', 'word_info': existing_word})
    else:
        c.execute('INSERT INTO shona_words (word, meaning_1, meaning_2, similar_words, example_sentence) VALUES (?, ?, ?, ?, ?)',
                  (word_data['word'], word_data['meaning_1'], word_data.get('meaning_2'), word_data['similar_words'], word_data.get('example_sentence')))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Word added successfully'})

@app.route('/edit_word/<int:word_id>', methods=['PUT'])
def edit_word(word_id):
    word_data = request.json
    if not word_data:
        return jsonify({'message': 'No data provided'})

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('UPDATE shona_words SET meaning_1=?, meaning_2=?, similar_words=?, example_sentence=? WHERE id=?',
              (word_data['meaning_1'], word_data.get('meaning_2'), word_data['similar_words'], word_data.get('example_sentence'), word_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Word updated successfully'})

@app.route('/get_words', methods=['GET'])
def get_words():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT * FROM shona_words')
    words = c.fetchall()
    conn.close()
    return jsonify({'words': words})

@app.route('/delete_word/<word>', methods=['DELETE'])
def delete_word(word):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM shona_words WHERE word = ?", (word,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Word deleted successfully'})

@app.route('/get_word/<word>', methods=['GET'])
def get_word(word):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT * FROM shona_words WHERE word=?', (word,))
    word_data = c.fetchone()

    if word_data:
        word_info = {
            'word': word_data[1],
            'meaning_1': word_data[2],
            'meaning_2': word_data[3],
            'similar_words': word_data[4],
            'example_sentence': word_data[5]
        }
        return jsonify(word_info)
    else:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT word FROM shona_words')
        all_words = c.fetchall()
        conn.close()

        all_words = [w[0] for w in all_words]
        word_lower = word.lower()
        close_matches = difflib.get_close_matches(word_lower, all_words, n=5)

        if word_lower in all_words:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute('SELECT * FROM shona_words WHERE word=?', (word_lower,))
            word_data = c.fetchone()
            conn.close()

            word_info = {
                'word': word_data[1],
                'meaning_1': word_data[2],
                'meaning_2': word_data[3],
                'similar_words': word_data[4],
                'example_sentence': word_data[5]
            }
            return jsonify(word_info)
        elif close_matches:
            return jsonify({'message': f'Word not found. Did you mean: {", ".join(close_matches)}?'})
        else:
            return jsonify({'message': 'Word not found'})

if __name__ == '__main__':
    load_shona('shona_words.json', db_path)
    app.run(debug=False)