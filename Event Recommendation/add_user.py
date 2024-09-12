import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Connect to the SQLite database
conn = sqlite3.connect('database/events.db')
c = conn.cursor()

# Define user data (replace with actual user info)
username = 'PW'
password = hash_password('pw')  # Make sure to hash the password
interests = 'technology, music, fitness'  # Comma-separated interests
is_admin = 0  # Set to 0 for a regular user, 1 for an admin

# Insert the new user into the 'users' table
c.execute("INSERT INTO users (username, password, interests, is_admin) VALUES (?, ?, ?, ?)",
          (username, password, interests, is_admin))

# Commit the transaction and close the connection
conn.commit()
conn.close()

print("User added successfully.")
