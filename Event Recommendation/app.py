from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize database
def init_db():
    conn = sqlite3.connect('database/events.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT NOT NULL, 
                  password TEXT NOT NULL, 
                  is_admin INTEGER NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT NOT NULL, 
                  description TEXT NOT NULL,
                  organizer TEXT NOT NULL, 
                  date TEXT NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS participation
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id INTEGER NOT NULL, 
                  event_id INTEGER NOT NULL,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (event_id) REFERENCES events (id))''')
    
    conn.commit()
    conn.close()

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Home route
@app.route('/')
def index():
    if 'username' in session:
        conn = sqlite3.connect('database/events.db')
        c = conn.cursor()
        c.execute("SELECT * FROM events")
        events = c.fetchall()
        conn.close()
        return render_template('index.html', events=events)
    else:
        return redirect(url_for('login'))

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        
        conn = sqlite3.connect('database/events.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            session['user_id'] = user[0]
            session['is_admin'] = user[3]  # Store admin status
            return redirect(url_for('index'))
        else:
            flash('Invalid login credentials')
    
    return render_template('login.html')

# User signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        interests = request.form['interests']

        conn = sqlite3.connect('database/events.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, is_admin,interests) VALUES (?, ?, 0, ?)", (username, password,interests))
        conn.commit()
        conn.close()
        
        flash('Signup successful! You can now log in.')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/signup/admin', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        
        conn = sqlite3.connect('database/events.db')
        c = conn.cursor()
        # Set is_admin = 1 for the admin user
        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, 1)", (username, password))
        conn.commit()
        conn.close()
        
        flash('Admin signup successful! You can now log in.')
        return redirect(url_for('login'))
    
    return render_template('signup.html')


# Admin event submission route
@app.route('/submit_event', methods=['GET', 'POST'])
def submit_event():
    if 'is_admin' in session and session['is_admin'] == 1:
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            organizer = request.form['organizer']
            date = request.form['date']
            
            conn = sqlite3.connect('database/events.db')
            c = conn.cursor()
            c.execute("INSERT INTO events (title, description, organizer, date) VALUES (?, ?, ?, ?)",
                      (title, description, organizer, date))
            conn.commit()
            conn.close()
            
            flash('Event successfully added')
            return redirect(url_for('index'))
        
        return render_template('submit_event.html')
    else:
        flash('You do not have access to add events')
        return redirect(url_for('index'))

@app.route('/event/<int:event_id>')
def event(event_id):
    conn = sqlite3.connect('database/events.db')
    c = conn.cursor()
    # Fetch the event details from the database
    c.execute("SELECT * FROM events WHERE id=?", (event_id,))
    event = c.fetchone()
    conn.close()

    if event:
        return render_template('event.html', event=event)
    else:
        flash('Event not found.')
        return redirect(url_for('index'))

@app.route('/participate/<int:event_id>', methods=['POST'])
def participate(event_id):
    if 'user_id' not in session:
        flash("You need to be logged in to participate.")
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = sqlite3.connect('database/events.db')
    c = conn.cursor()

    # Check if the user has already participated in this event
    c.execute("SELECT * FROM participation WHERE user_id=? AND event_id=?", (user_id, event_id))
    participation = c.fetchone()

    if participation:
        flash("You have already registered for this event.")
    else:
        # Register user for the event
        c.execute("INSERT INTO participation (user_id, event_id) VALUES (?, ?)", (user_id, event_id))
        conn.commit()
        flash("Successfully registered for the event!")
    
    conn.close()

    return redirect(url_for('event', event_id=event_id))


# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect(url_for('login'))

def calculate_similarity(text1, text2):
    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()
    similarity = cosine_similarity([vectors[0]], [vectors[1]])
    print(f"{text1}-{text2},{similarity}")
    print()
    return similarity[0][0]

def recommend_events(user_id):
    conn = sqlite3.connect('database/events.db')
    c = conn.cursor()

    # Fetch the user's interests
    c.execute("SELECT interests FROM users WHERE id=?", (user_id,))
    result = c.fetchone()

    if result is None:
        # Handle case where the user is not found or has no interests
        flash("No interests found for the user.")
        return []

    user_interests = result[0]

    # Fetch all events
    c.execute("SELECT id, title, description FROM events")
    all_events = c.fetchall()

    # Threshold for similarity
    similarity_threshold = 0.2
    recommended_events = []

    c.execute("SELECT event_id FROM participation WHERE user_id=?", (user_id,))
    past_participation = [row[0] for row in c.fetchall()]

    for event in all_events:
        event_id, title, description = event
        event_text = f"{title} "

        # Calculate similarity between interests and event text
        similarity = calculate_similarity(user_interests, event_text)

        # If similarity is above threshold, recommend the event
        if similarity >= similarity_threshold:
            recommended_events.append(event)

        # If the event was attended before, prioritize it
        if event_id in past_participation:
            recommended_events.insert(0, event)  # Prioritize by placing at the front

    conn.close()

    return recommended_events

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    print(user_id)
    recommended_events = recommend_events(user_id)

    return render_template('dashboard.html', recommended_events=recommended_events)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
