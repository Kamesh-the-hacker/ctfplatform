import sqlite3

db = sqlite3.connect("database.db")
c = db.cursor()

c.executescript("""

CREATE TABLE users (
 id INTEGER PRIMARY KEY,
 username TEXT,
 password TEXT,
 team_id INTEGER
);

CREATE TABLE teams (
 id INTEGER PRIMARY KEY,
 name TEXT,
 password TEXT,
 score INTEGER DEFAULT 0
);

CREATE TABLE challenges (
 id INTEGER PRIMARY KEY,
 title TEXT,
 category TEXT,
 description TEXT,
 flag TEXT,
 points INTEGER,
 file TEXT
);

CREATE TABLE submissions (
 id INTEGER PRIMARY KEY,
 user_id INTEGER,
 challenge_id INTEGER,
 correct INTEGER
);

CREATE TABLE admin (
 id INTEGER PRIMARY KEY,
 username TEXT,
 password TEXT
);

INSERT INTO admin(username,password) VALUES('admin','admin123');

""")

db.commit()
db.close()