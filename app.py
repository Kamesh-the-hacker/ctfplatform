from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secretkey"

UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ---------------- DB ----------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row   # 🔥 use column names instead of index
    return conn


# ---------------- AUTH ----------------
@app.route('/')
def home():
    if 'user' in session:
        return redirect('/dashboard')
    return redirect('/login')


from flask import flash

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']

        # validation
        if len(u) < 8 or len(p) < 8:
            return render_template('register.html', msg="❌ Minimum 8 characters required")

        db = get_db()

        # check existing
        existing = db.execute(
            "SELECT * FROM users WHERE username=?", (u,)
        ).fetchone()

        if existing:
            return render_template('register.html', msg="❌ Username already taken")

        # create account
        db.execute(
            "INSERT INTO users(username,password) VALUES (?,?)",
            (u, p)
        )
        db.commit()

        # 🔥 SUCCESS → redirect to login
        flash("✅ Account created successfully! Please login.")

        return redirect('/login')

    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ""

    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (u, p)
        ).fetchone()

        if user:
            session['user'] = user['id']

            # 🔥 check team
            if user['team_id'] is None:
                return redirect('/team')   # go create/join team
            else:
                return redirect('/dashboard')  # already in team

        else:
            msg = "❌ Wrong username or password"

    return render_template('login.html', msg=msg)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()

    challenges = db.execute("SELECT * FROM challenges").fetchall()

    solved = db.execute("""
        SELECT challenge_id FROM submissions
        WHERE user_id=? AND correct=1
    """, (session['user'],)).fetchall()

    solved_ids = [s['challenge_id'] for s in solved]

    # 🔥 GROUP BY CATEGORY
    grouped = {}
    for c in challenges:
        cat = c['category']
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(c)

    return render_template(
        'dashboard.html',
        grouped=grouped,
        solved_ids=solved_ids
    )

# ---------------- TEAM ----------------
@app.route('/team')
def team():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()

    team_id = db.execute(
        "SELECT team_id FROM users WHERE id=?",
        (session['user'],)
    ).fetchone()['team_id']

    if team_id:
        team = db.execute(
            "SELECT * FROM teams WHERE id=?", (team_id,)
        ).fetchone()

        members = db.execute(
            "SELECT username FROM users WHERE team_id=?", (team_id,)
        ).fetchall()

        return render_template('team.html', team=team, members=members)

    return render_template('team.html', team=None)


@app.route('/create_team', methods=['GET', 'POST'])
def create_team():
    if 'user' not in session:
        return redirect('/login')

    msg = ""

    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        # 🔒 validation
        if len(password) < 3:
            msg = "❌ Team password must be at least 3 characters"
            return render_template('create_team.html', msg=msg)

        db = get_db()

        # optional: check duplicate team name
        existing = db.execute(
            "SELECT * FROM teams WHERE name=?", (name,)
        ).fetchone()

        if existing:
            msg = "❌ Team name already exists"
            return render_template('create_team.html', msg=msg)

        # create team
        db.execute(
            "INSERT INTO teams(name,password) VALUES(?,?)",
            (name, password)
        )
        db.commit()

        team_id = db.execute(
            "SELECT id FROM teams WHERE name=?", (name,)
        ).fetchone()['id']

        db.execute(
            "UPDATE users SET team_id=? WHERE id=?",
            (team_id, session['user'])
        )
        db.commit()

        return redirect('/dashboard')

    return render_template('create_team.html', msg=msg)
@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
def edit_challenge(id):
    if 'admin' not in session:
        return redirect('/admin_login')

    db = get_db()

    # get challenge
    c = db.execute(
        "SELECT * FROM challenges WHERE id=?", (id,)
    ).fetchone()

    if not c:
        return "Challenge not found"

    if request.method == 'POST':
        db.execute("""
            UPDATE challenges
            SET title=?, category=?, description=?, flag=?, points=?
            WHERE id=?
        """, (
            request.form['title'],
            request.form['category'],
            request.form['desc'],
            request.form['flag'],
            int(request.form['points']),
            id
        ))
        db.commit()

        return redirect('/admin/challenges')

    return render_template('edit_challenge.html', c=c)
@app.route('/admin/live_scoreboard')
def live_scoreboard():
    if 'admin' not in session:
        return redirect('/admin_login')
    return render_template('live_scoreboard.html')

@app.route('/api/scoreboard')
def api_scoreboard():
    db = get_db()

    teams = db.execute("""
        SELECT name, score
        FROM teams
        ORDER BY score DESC
    """).fetchall()

    return {"teams": [dict(t) for t in teams]}
@app.route('/admin/live')
def admin_live():
    if 'admin' not in session:
        return redirect('/admin_login')

    return render_template('admin_live.html')
@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if 'admin' not in session:
        return redirect('/admin_login')

    db = get_db()
    msg = ""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db.execute("""
            UPDATE admin
            SET username=?, password=?
        """, (username, password))
        db.commit()

        msg = "✅ Updated successfully"

    admin = db.execute("SELECT * FROM admin").fetchone()

    return render_template('admin_settings.html', admin=admin, msg=msg)

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/join_team', methods=['GET', 'POST'])
def join_team():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    msg = ""

    # 🔢 count teams
    count = db.execute("SELECT COUNT(*) as total FROM teams").fetchone()['total']

    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        team = db.execute(
            "SELECT * FROM teams WHERE name=?", (name,)
        ).fetchone()

        if not team:
            msg = "❌ Team not found"

        elif team['password'] != password:
            msg = "❌ Wrong team password"

        else:
            db.execute(
                "UPDATE users SET team_id=? WHERE id=?",
                (team['id'], session['user'])
            )
            db.commit()

            return redirect('/dashboard')

    return render_template('join_team.html', msg=msg, count=count)


# ---------------- CHALLENGE ----------------
@app.route('/challenge/<int:id>', methods=['GET', 'POST'])
def challenge(id):
    db = get_db()
    c = db.execute("SELECT * FROM challenges WHERE id=?", (id,)).fetchone()

    if not c:
        return "Challenge not found"

    msg = ""

    if request.method == 'POST':
        flag = request.form['flag']

        solved = db.execute(
            "SELECT * FROM submissions WHERE user_id=? AND challenge_id=? AND correct=1",
            (session['user'], id)
        ).fetchone()

        if solved:
            msg = "Already solved!"
        else:
            if flag == c['flag']:
                db.execute(
                    "INSERT INTO submissions(user_id,challenge_id,correct) VALUES (?,?,1)",
                    (session['user'], id)
                )

                team_id = db.execute(
                    "SELECT team_id FROM users WHERE id=?",
                    (session['user'],)
                ).fetchone()['team_id']

                if team_id:
                    db.execute(
                        "UPDATE teams SET score = score + ? WHERE id=?",
                        (c['points'], team_id)
                    )

                db.commit()
                msg = "✅ Correct!"
            else:
                msg = "❌ Wrong flag"

    return render_template('challenge.html', c=c, msg=msg)


# ---------------- FILE DOWNLOAD ----------------
@app.route('/files/<filename>')
def download_file(filename):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True
    )


# ---------------- SCOREBOARD ----------------
@app.route('/scoreboard')
def scoreboard():
    db = get_db()
    teams = db.execute(
        "SELECT name, score FROM teams ORDER BY score DESC"
    ).fetchall()

    return render_template('scoreboard.html', teams=teams)


# ---------------- PROFILE ----------------
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()

    user = db.execute(
        "SELECT * FROM users WHERE id=?",
        (session['user'],)
    ).fetchone()

    team = None
    members = []

    if user['team_id']:
        team = db.execute(
            "SELECT * FROM teams WHERE id=?",
            (user['team_id'],)
        ).fetchone()

        members = db.execute(
            "SELECT username FROM users WHERE team_id=?",
            (user['team_id'],)
        ).fetchall()

    solved = db.execute("""
        SELECT challenges.title FROM submissions
        JOIN challenges ON submissions.challenge_id = challenges.id
        WHERE submissions.user_id=? AND correct=1
    """, (session['user'],)).fetchall()

    return render_template(
        'profile.html',
        user=user,
        team=team,
        members=members,
        solved=solved
    )


# ---------------- ADMIN ----------------
def is_admin():
    return 'admin' in session


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']

        db = get_db()
        admin = db.execute(
            "SELECT * FROM admin WHERE username=? AND password=?",
            (u, p)
        ).fetchone()

        if admin:
            session['admin'] = True
            return redirect('/admin')

    return render_template('admin_login.html')


@app.route('/admin')
def admin_dashboard():
    if not is_admin():
        return redirect('/admin_login')

    return render_template('admin_dashboard.html')


# -------- USERS --------
@app.route('/admin/users')
def admin_users():
    if not is_admin():
        return redirect('/admin_login')

    users = get_db().execute("SELECT * FROM users").fetchall()
    return render_template('admin_users.html', users=users)


@app.route('/admin/delete_user/<int:id>')
def delete_user(id):
    if not is_admin():
        return redirect('/admin_login')

    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (id,))
    db.commit()
    return redirect('/admin/users')


# -------- TEAMS --------
@app.route('/admin/teams')
def admin_teams():
    if not is_admin():
        return redirect('/admin_login')

    teams = get_db().execute("SELECT * FROM teams").fetchall()
    return render_template('admin_teams.html', teams=teams)


@app.route('/admin/delete_team/<int:id>')
def delete_team(id):
    if not is_admin():
        return redirect('/admin_login')

    db = get_db()
    db.execute("DELETE FROM teams WHERE id=?", (id,))
    db.commit()
    return redirect('/admin/teams')


# -------- CHALLENGES --------
@app.route('/admin/challenges', methods=['GET', 'POST'])
def admin_challenges():
    if not is_admin():
        return redirect('/admin_login')

    db = get_db()

    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        desc = request.form['desc']
        flag = request.form['flag']
        points = int(request.form['points'])

        file = request.files['file']
        filename = ""

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        db.execute("""
            INSERT INTO challenges(title,category,description,flag,points,file)
            VALUES (?,?,?,?,?,?)
        """, (title, category, desc, flag, points, filename))

        db.commit()

    challenges = db.execute("SELECT * FROM challenges").fetchall()
    return render_template('admin_challenges.html', challenges=challenges)


@app.route('/admin/delete_challenge/<int:id>')
def delete_challenge(id):
    if not is_admin():
        return redirect('/admin_login')

    db = get_db()
    db.execute("DELETE FROM challenges WHERE id=?", (id,))
    db.commit()
    return redirect('/admin/challenges')


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)