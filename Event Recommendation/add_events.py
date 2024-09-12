import sqlite3

# Connect to the database
conn = sqlite3.connect('database/events.db')
c = conn.cursor()

# Sample events to insert
events = [
    ("Tech Conference 2024", "A conference for tech enthusiasts to learn about the latest trends in technology.", "Tech Corp", "2024-09-15"),
    ("Music Festival", "Join us for a weekend of music, food, and fun at the annual music festival.", "Music World", "2024-10-05"),
    ("Startup Pitch Night", "An event where startups pitch their ideas to potential investors.", "Startup Hub", "2024-09-25"),
    ("Art Exhibition", "Showcasing modern art from up-and-coming artists around the world.", "Art Gallery", "2024-11-01"),
    ("Business Workshop", "Learn effective business strategies from industry leaders.", "Biz Leaders", "2024-09-20"),
    ("Fitness Bootcamp", "A week-long fitness program for all fitness levels.", "FitLife", "2024-10-12"),
    ("Film Screening", "A special screening of an indie film followed by a Q&A with the director.", "Film Studio", "2024-09-18"),
    ("Community Charity Event", "A charity event to raise funds for local causes.", "Local Heroes", "2024-11-05")
]

# Insert events into the 'events' table
c.executemany("INSERT INTO events (title, description, organizer, date) VALUES (?, ?, ?, ?)", events)

# Commit and close the connection
conn.commit()
conn.close()

print("8 events added successfully.")
