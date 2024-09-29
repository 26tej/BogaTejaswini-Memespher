from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector.pooling
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure secret key for sessions

# Database connection pooling
db_config = {
    'host': 'database-1.c5umwy80wkmu.eu-north-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Tejaswini26',
    'database': 'memesphere'
}

# Create a MySQL connection pool
cnxpool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **db_config)

def get_db_connection():
    """ Get a database connection from the pool """
    try:
        return cnxpool.get_connection()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Route to display the index page
@app.route('/')
def index():
    return render_template('index.html')

# Register Route
# @app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", 
                               (username, email, password_hash))
                connection.commit()
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for('login'))
            except mysql.connector.Error as err:
                flash(f"Error: {err}", "danger")
            finally:
                cursor.close()
                connection.close()
        else:
            flash("Database connection failed!", "danger")
    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT id, password_hash, login_count FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()

                if user:
                    stored_password_hash = user[1]

                    # Check if the entered password matches the stored hash
                    if check_password_hash(stored_password_hash, password):
                        session['user_id'] = user[0]
                        session['username'] = username

                        # Update login count
                        new_login_count = user[2] + 1
                        cursor.execute("UPDATE users SET login_count = %s WHERE id = %s", (new_login_count, user[0]))
                        connection.commit()

                        flash("Login successful!", "success")
                        return redirect(url_for('meme_output'))
                    else:
                        flash("Invalid credentials. Please try again.", "danger")
                else:
                    flash("User not found. Please check your username.", "danger")
            except mysql.connector.Error as err:
                flash(f"Error: {err}", "danger")
            finally:
                cursor.close()
                connection.close()
        else:
            flash("Database connection failed!", "danger")
    return render_template('login.html')

# Route to display the meme output page
@app.route('/meme_output')
def meme_output():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('meme_output.html')

# Route to handle meme search
@app.route('/search_meme', methods=['POST'])
def search_meme():
    emotion = request.form['emotion'].lower()

    if 'user_id' in session:
        user_id = session['user_id']
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("INSERT INTO meme_searches (user_id, emotion) VALUES (%s, %s)", (user_id, emotion))
        connection.commit()

        cursor.close()
        connection.close()

    memes = {
        'anger': ['../static/images/anger/anger1.jpeg', '../static/images/anger/anger2.jpg', '../static/images/anger/anger3.jpeg'],
        'fear': ['../static/images/fear/fear1.png', '../static/images/fear/fear2.jpg', '../static/images/fear/fear3.jpg'],
        'surprise': ['../static/images/surprise/surprise1.jpeg', '../static/images/surprise/surprise2.jpg', '../static/images/surprise/surprise3.jpg'],
        'happiness': ['../static/images/happiness/happiness1.jpeg', '../static/images/happiness/happiness2.jpg', '../static/images/happiness/happiness3.jpg'],
        'sadness': ['../static/images/sadness/sadness1.jpeg', '../static/images/sadness/sadness2.jpg', '../static/images/sadness/sadness3.jpg'],
        'cry': ['../static/images/cry/cry1.jpeg', '../static/images/cry/cry2.jpeg', '../static/images/cry/cry3.jpeg'],
        'funny': ['../static/images/funny/funny1.jpg', '../static/images/funny/funny2.jpeg', '../static/images/funny/funny3.jpg'],
        'sarcasm': ['../static/images/sarcasm/sarcasm1.jpeg', '../static/images/sarcasm/sarcasm2.jpeg', '../static/images/sarcasm/sarcasm3.jpg']
    }

    meme_images = memes.get(emotion, [])
    return render_template('meme_output.html', meme_images=meme_images, emotion=emotion)

if __name__ == '__main__':
    app.run(debug=True)
