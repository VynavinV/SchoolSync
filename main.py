from flask import Flask, render_template, redirect, url_for, request, session, flash, g, jsonify
from werkzeug.utils import secure_filename
import os
import sqlite3
from PIL import Image
from google_auth_oauthlib.flow import Flow 
import pathlib
import requests
import cachecontrol
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
import google
from google.oauth2 import id_token
import re
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler


login = False
app = Flask(__name__)
app.secret_key = 'hbswitchschoolsync'  # Change 'your_secret_key' to a real secret key
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CLIENT_ID = '997541497690-6rtqkfqe4gfdfdf0bo1gt7s79polqh6n.apps.googleusercontent.com'
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, 'client_secret.json')
request_session = requests.Session()

flow = Flow.from_client_secrets_file(client_secrets_file=client_secrets_file, 
                                     scopes=['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email',"openid"],
                                     redirect_uri='http://127.0.0.1:5001/callback'
                                     )

# Ensure the UPLOAD_FOLDER existss
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image_path, output_size=(2560, 1707)):
    with Image.open(image_path) as img:
        img = img.resize(output_size, Image.LANCZOS)
        img.save(image_path)

def initialize_database():
    conn = get_db_connection()
    with open('schema.sql') as f:
        conn.executescript(f.read())
    conn.close()

@app.before_request
def before_request():
    if not hasattr(g, 'db_initialized'):
        initialize_database()
        g.db_initialized = True
        
@app.route('/highscore', methods=['GET', 'POST'])
def highscore():
    conn = get_db_connection()
    if request.method == 'POST':
        new_score = request.json.get('score')
        if new_score is None:
            return jsonify({'error': 'Score is required'}), 400

        new_score = int(new_score)

        # Retrieve the existing high score (numerical part only)
        existing_high_score = conn.execute('SELECT MAX(CAST(SUBSTR(score, 1, INSTR(score, " by ")-1) AS INTEGER)) AS high_score FROM high_scores').fetchone()['high_score']

        # Insert new high score if it's higher than the existing one
        if existing_high_score is None or new_score > existing_high_score:
            user_name = session.get('user_name', 'Anonymous')
            nw = f"{new_score} by {user_name}"
            conn.execute('INSERT INTO high_scores (score) VALUES (?)', (nw,))
            conn.commit()

        return jsonify({'message': 'High score updated'})

    elif request.method == 'GET':
        high_score = conn.execute('SELECT MAX(CAST(SUBSTR(score, 1, INSTR(score, " by ")-1) AS INTEGER)) AS high_score FROM high_scores').fetchone()['high_score']
        if high_score is None:
            high_score = '0' 
        return jsonify({'high_score': high_score})

    
@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))

    user_email = session.get('user_email')

    # Connect to the database
    conn = get_db_connection()

    # Fetch user role
    user_role_row = conn.execute('SELECT user_role FROM users WHERE user_email = ?', (user_email,)).fetchone()
    user_role = user_role_row['user_role'] if user_role_row else 'student'
    session['user_role'] = user_role

    # Fetch clubs data from the database
    clubs = conn.execute('SELECT * FROM clubs').fetchall()

    # Fetch events from the database
    events = conn.execute('SELECT * FROM events').fetchall()

    user_pfp = session.get('user_pfp')  # Get the user profile picture URL
    conn.close()

    # Render the template with the user's role, profile picture, clubs, and events
    return render_template('index.html', clubs=clubs, user_role=user_role, user_pfp=user_pfp, events=events)
import random


@app.route('/mobileclubs')
def mobileclubs():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))

    user_email = session.get('user_email')

    # Connect to the database
    conn = get_db_connection()

    # Fetch user role
    user_role_row = conn.execute('SELECT user_role FROM users WHERE user_email = ?', (user_email,)).fetchone()
    user_role = user_role_row['user_role'] if user_role_row else 'student'
    session['user_role'] = user_role

    # Fetch clubs data from the database
    clubs = conn.execute('SELECT * FROM clubs').fetchall()

    # Fetch events from the database
    events = conn.execute('SELECT * FROM events').fetchall()

    user_pfp = session.get('user_pfp')  # Get the user profile picture URL
    conn.close()

    # Render the template with the user's role, profile picture, clubs, and events
    return render_template('index.html', clubs=clubs, user_role=user_role, user_pfp=user_pfp, events=events)
import random
@app.route('/mobile')
def mobile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))

    user_email = session.get('user_email')
    user_name = session.get('name', '').replace('Harold M Brathwaite SS', '')

    # Connect to the database
    conn = get_db_connection()

    # Fetch user role
    user_role_row = conn.execute('SELECT user_role FROM users WHERE user_email = ?', (user_email,)).fetchone()
    user_role = user_role_row['user_role'] if user_role_row else 'student'
    session['user_role'] = user_role

    # Fetch clubs data from the database, excluding the "Public" club
    clubs = conn.execute('SELECT * FROM clubs WHERE name != "Public" ORDER BY RANDOM() LIMIT 5').fetchall()

    # Fetch the latest 5 events for the carousel
    events = conn.execute('SELECT * FROM events ORDER BY event_date LIMIT 5').fetchall()

    user_pfp = session.get('user_pfp')  # Get the user profile picture URL
    conn.close()

    # Render the template with the user's role, profile picture, clubs, and events
    return render_template('indexmobile.html', clubs=clubs, user_role=user_role, user_pfp=user_pfp, events=events, user_name=user_name)


@app.route('/dash')
def dash():
    # Render the template with the user's role and profile picture
    return render_template('dash.html')


@app.route('/dino')
def dino():
    # Render the template with the user's role and profile picture
    return render_template('Dino.html')

@app.route('/allClubs', methods=['GET'])
def allClubs():
    view_type = request.args.get('view-type', 'clubs')
    search_query = request.args.get('search', '').strip()
    selected_category = request.args.get('category', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    
    # Fetch all unique categories for the dropdown
    categories = [row[0] for row in conn.execute('SELECT DISTINCT category FROM clubs').fetchall()]

    if view_type == 'clubs':
        query = 'SELECT * FROM clubs WHERE 1=1'
        params = []
        
        if search_query:
            query += ' AND name LIKE ?'
            params.append('%' + search_query + '%')
        
        if selected_category:
            query += ' AND category = ?'
            params.append(selected_category)
        
        total_entries_query = 'SELECT COUNT(*) FROM clubs WHERE 1=1'
        total_params = params.copy()
        
        total_entries = conn.execute(total_entries_query + query[len('SELECT * FROM clubs WHERE 1=1'):], tuple(total_params)).fetchone()[0]
        
        query += ' LIMIT ? OFFSET ?'
        params.extend([per_page, offset])
        
        data = conn.execute(query, tuple(params)).fetchall()
        
    elif view_type == 'members':
        if search_query:
            total_entries = conn.execute('SELECT COUNT(*) FROM users WHERE user_name LIKE ? OR user_email LIKE ?', 
                                         ('%' + search_query + '%', '%' + search_query + '%')).fetchone()[0]
            data = conn.execute('SELECT user_name, user_email, user_role FROM users WHERE user_name LIKE ? OR user_email LIKE ? LIMIT ? OFFSET ?', 
                                ('%' + search_query + '%', '%' + search_query + '%', per_page, offset)).fetchall()
        else:
            total_entries = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            data = conn.execute('SELECT user_name, user_email, user_role FROM users LIMIT ? OFFSET ?', 
                                (per_page, offset)).fetchall()
    
    conn.close()
    
    total_pages = (total_entries + per_page - 1) // per_page  # Calculate total pages
    
    return render_template('allClubs.html', 
                           clubs=data if view_type == 'clubs' else None, 
                           members=data if view_type == 'members' else None, 
                           categories=categories,
                           selected_category=selected_category,
                           view_type=view_type,
                           page=page,
                           search_query=search_query,
                           total_pages=total_pages)


@app.route('/editClub/<int:club_id>', methods=['GET', 'POST'])
def editClub(club_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))
    if session['user_role'] != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()

    # Fetch the selected club data
    club = conn.execute('SELECT * FROM clubs WHERE id = ?', (club_id,)).fetchone()
    
    # Check if the club exists and its name is not "Public"
    if not club:
        flash('Club not found.')
        return redirect(url_for('allClubs'))
    
    if club['name'] == 'Public':
        flash('Editing the "Public" club is not allowed.')
        return redirect(url_for('allClubs'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        file = request.files['image']

        # Check if the club name is unique
        existing_club = conn.execute('SELECT * FROM clubs WHERE name = ? AND id != ?', (name, club_id)).fetchone()
        if existing_club:
            flash('Club name already exists. Please choose a different name.')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            resize_image(filepath)  # Resize the image
            image_url = 'uploads/' + filename

            conn.execute('UPDATE clubs SET name = ?, description = ?, category = ?, image_url = ? WHERE id = ?',
                         (name, description, category, image_url, club_id))
        else:
            conn.execute('UPDATE clubs SET name = ?, description = ?, category = ? WHERE id = ?',
                         (name, description, category, club_id))

        conn.commit()
        conn.close()
        return redirect(url_for('allClubs'))

    # Fetch all clubs for the dropdown
    clubs = conn.execute('SELECT id, name FROM clubs').fetchall()
    conn.close()

    return render_template('editClub.html', club=club, clubs=clubs)



@app.route('/delete_club', methods=['POST'])
def delete_club():
    conn = get_db_connection()
    user_email = session.get('user_email')
    user_role_row = conn.execute('SELECT user_role FROM users WHERE user_email = ?', (user_email,)).fetchone()
    
    if user_role_row:
        user_role = user_role_row['user_role']
        # Update the session with the correct user role
        session['user_role'] = user_role
    else:
        # Default to 'student' if user role not found in the database
        session['user_role'] = 'student'
        user_role = 'student'
    
    club_id = request.form.get('club_id')
    category = request.form.get('category')  # Get the category from the form
    
    if club_id:
        # Fetch the club details to check its name
        club = conn.execute('SELECT name FROM clubs WHERE id = ?', (club_id,)).fetchone()
        
        if club:
            if club['name'] == 'Public':
                flash('Deleting the "Public" club is not allowed.', 'error')
            else:
                # Deleting the club from the database
                conn.execute('DELETE FROM clubs WHERE id = ?', (club_id,))
                conn.commit()
                flash('Club deleted successfully!', 'success')
        else:
            flash('Club not found.', 'error')
        
        conn.close()
    else:
        flash('Failed to delete the club. Club ID not provided.', 'error')
    
    # Redirect back to the correct category page
    return redirect(url_for('tech', category=category))


@app.route('/delete_club1', methods=['POST'])
def delete_club1():
    conn = get_db_connection()
    user_email = session.get('user_email')
    user_role_row = conn.execute('SELECT user_role FROM users WHERE user_email = ?', (user_email,)).fetchone()
    
    if user_role_row:
        user_role = user_role_row['user_role']
        # Update the session with the correct user role
        session['user_role'] = user_role
    else:
        # Default to 'student' if user role not found in the database
        session['user_role'] = 'student'
        user_role = 'student'
    club_id = request.form.get('club_id')
    category = request.form.get('category')  # Get the category from the form
    
    if club_id:
        conn = get_db_connection()
        cur = conn.cursor()
        # Deleting the club from the database
        cur.execute('DELETE FROM clubs WHERE id = ?', (club_id,))
        conn.commit()
        conn.close()
        
        flash('Club deleted successfully!', 'success')
    else:
        flash('Failed to delete the club. Club ID not provided.', 'error')
    
    # Redirect back to the ALL clubs page
    return redirect(url_for('allClubs'))
@app.route('/error')
def error():
    return render_template('error.html')

@app.route('/tech', methods=['GET'])
@app.route('/tech/<category>', methods=['GET'])
def tech(category=None):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))



    conn = get_db_connection()

    # Sanitize category value (remove special characters if necessary)
    if category:
        category = category.replace('<', '').replace('>', '')  # Remove special characters
        clubs = conn.execute("SELECT * FROM clubs WHERE category = ?", (category,)).fetchall()
    else:
        clubs = conn.execute("SELECT * FROM clubs WHERE category = 'Tech'").fetchall()

    user_email = session.get('user_email')
    registered_clubs = set()
    user_role = 'student'  # Default role

    if user_email:
        user = conn.execute('SELECT user_id, user_role FROM users WHERE user_email = ?', (user_email,)).fetchone()
        if user:
            user_id = user['user_id']
            user_role = user['user_role']
            registrations = conn.execute('SELECT club_id FROM clublink WHERE user_id = ?', (user_id,)).fetchall()
            registered_clubs = {row['club_id'] for row in registrations}

    clubs_with_status = []
    for club in clubs:
        club_dict = dict(club)
        club_dict['registered'] = club['id'] in registered_clubs
        club_dict['user_role'] = user_role
        clubs_with_status.append(club_dict)

    conn.close()
    return render_template('tech.html', tech_clubs=clubs_with_status, category=category or 'Tech', user_role=user_role)


@app.route('/Search', methods=['GET'])
@app.route('/Search/<category>', methods=['GET'])
def Search(category=None):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))



    conn = get_db_connection()

    # Sanitize category value (remove special characters if necessary)
    if category:
        category = category.replace('<', '').replace('>', '')  # Remove special characters
        clubs = conn.execute("SELECT * FROM clubs WHERE name LIKE ?", ('%' + category + '%',)).fetchall()
    else:
        clubs = conn.execute("SELECT * FROM clubs WHERE name LIKE 'Public'").fetchall()

    user_email = session.get('user_email')
    registered_clubs = set()
    user_role = 'student'  # Default role

    if user_email:
        user = conn.execute('SELECT user_id, user_role FROM users WHERE user_email = ?', (user_email,)).fetchone()
        if user:
            user_id = user['user_id']
            user_role = user['user_role']
            registrations = conn.execute('SELECT club_id FROM clublink WHERE user_id = ?', (user_id,)).fetchall()
            registered_clubs = {row['club_id'] for row in registrations}

    clubs_with_status = []
    for club in clubs:
        club_dict = dict(club)
        club_dict['registered'] = club['id'] in registered_clubs
        club_dict['user_role'] = user_role
        clubs_with_status.append(club_dict)
    user_pfp = session.get('user_pfp')  # Get the user profile picture URL

    conn.close()
    return render_template('Search.html', tech_clubs=clubs_with_status, category=category or 'Public', user_role=user_role, user_pfp=user_pfp)


@app.route('/myclubsMOB', methods=['GET'])
@app.route('/myclubsMOB/', methods=['GET'])
def myclubsMOB():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    email = session.get('user_email')
    user = conn.execute('SELECT user_id FROM users WHERE user_email = ?', (email,)).fetchone()

    # Return clubs the user is in
    clubs = []
    if user:
        user_id = user['user_id']
        clubs = conn.execute('SELECT * FROM clubs WHERE id IN (SELECT club_id FROM clublink WHERE user_id = ?)', (user_id,)).fetchall()
    else:
        clubs = []  # No clubs if user is not found

    user_email = session.get('user_email')
    registered_clubs = set()
    user_role = 'student'  # Default role

    if user_email:
        user = conn.execute('SELECT user_id, user_role FROM users WHERE user_email = ?', (user_email,)).fetchone()
        if user:
            user_id = user['user_id']
            user_role = user['user_role']
            registrations = conn.execute('SELECT club_id FROM clublink WHERE user_id = ?', (user_id,)).fetchall()
            registered_clubs = {row['club_id'] for row in registrations}

    clubs_with_status = []
    for club in clubs:
        club_dict = dict(club)
        club_dict['registered'] = club['id'] in registered_clubs
        club_dict['user_role'] = user_role
        clubs_with_status.append(club_dict)

    conn.close()
    user_pfp = session.get('user_pfp')  # Get the user profile picture URL
    return render_template('myclubsMOB.html', clubs=clubs_with_status, user_role=user_role, user_pfp=user_pfp)


@app.route('/myclubs', methods=['GET'])
@app.route('/myclubs/', methods=['GET'])
def myclubs():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    email = session.get('user_email')
    user = conn.execute('SELECT user_id FROM users WHERE user_email = ?', (email,)).fetchone()

    # Return clubs the user is in
    clubs = []
    if user:
        user_id = user['user_id']
        clubs = conn.execute('SELECT * FROM clubs WHERE id IN (SELECT club_id FROM clublink WHERE user_id = ?)', (user_id,)).fetchall()
    else:
        clubs = []  # No clubs if user is not found

    user_email = session.get('user_email')
    registered_clubs = set()
    user_role = 'student'  # Default role

    if user_email:
        user = conn.execute('SELECT user_id, user_role FROM users WHERE user_email = ?', (user_email,)).fetchone()
        if user:
            user_id = user['user_id']
            user_role = user['user_role']
            registrations = conn.execute('SELECT club_id FROM clublink WHERE user_id = ?', (user_id,)).fetchall()
            registered_clubs = {row['club_id'] for row in registrations}

    clubs_with_status = []
    for club in clubs:
        club_dict = dict(club)
        club_dict['registered'] = club['id'] in registered_clubs
        club_dict['user_role'] = user_role
        clubs_with_status.append(club_dict)

    conn.close()
    print(clubs_with_status)
    return render_template('myclubs.html', clubs=clubs_with_status, user_role=user_role)




@app.route('/club/<int:club_id>')
def club_page(club_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))
    
    user_email = session.get('user_email')
    conn = get_db_connection()
    user = conn.execute('SELECT user_id, user_role FROM users WHERE user_email = ?', (user_email,)).fetchone()
    
    if user:
        user_role = user['user_role']
        user_id = user['user_id']

        # Check if the user is registered in the specific club
        registered = conn.execute('SELECT 1 FROM clublink WHERE club_id = ? AND user_id = ?', (club_id, user_id)).fetchone() is not None

        # Check if the user is an admin of the specific club
        clubrole = conn.execute('''
            SELECT role 
            FROM clublink 
            WHERE user_id = ? AND club_id = ? AND role = 'admin'
        ''', (user_id, club_id)).fetchone()

        # If the user is a site admin or a club admin for the specific club, redirect to manageClub
        if user_role == 'admin' or clubrole is not None:
            return redirect(url_for('manageClub', club_id=club_id))
        else:
            return redirect(url_for('Announcement', club_id=club_id))
    else:
        return redirect(url_for('login'))

@app.route('/club1/<int:club_id>')
def club_page1(club_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))
    
    user_email = session.get('user_email')
    conn = get_db_connection()
    user = conn.execute('SELECT user_id, user_role FROM users WHERE user_email = ?', (user_email,)).fetchone()
    
    if user:
        user_role = user['user_role']
        user_id = user['user_id']

        # Check if the user is registered in the specific club
        registered = conn.execute('SELECT 1 FROM clublink WHERE club_id = ? AND user_id = ?', (club_id, user_id)).fetchone() is not None

        # Check if the user is an admin of the specific club
        clubrole = conn.execute('''
            SELECT role 
            FROM clublink 
            WHERE user_id = ? AND club_id = ? AND role = 'admin'
        ''', (user_id, club_id)).fetchone()

        # If the user is a site admin or a club admin for the specific club, redirect to manageClub
        if user_role == 'admin' or clubrole is not None:
            return redirect(url_for('members', club_id=club_id))
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))



@app.route('/announcements.html/<int:club_id>', methods=['GET', 'POST'])
def Announcement(club_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))
    user_pfp = session.get('user_pfp')
    conn = get_db_connection()
    club = conn.execute('SELECT * FROM clubs WHERE id = ?', (club_id,)).fetchone()
    if not club:
        conn.close()
        return 'Club not found', 404

    if request.method == 'POST':
        if 'announcement' in request.form:
            announcement = request.form['announcement']
            created_by = session.get('user_name')
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute('INSERT INTO announcements (club_id, announcement, created_by, created_at) VALUES (?, ?, ?, ?)', 
                         (club_id, announcement, created_by, created_at))
            conn.commit()

    # Fetch the latest 30 announcements along with the user's name and profile picture
    club_announcements = conn.execute('''
        SELECT a.announcement, a.created_at, u.user_name, u.user_pfp 
        FROM announcements a
        JOIN users u ON a.created_by = u.user_name
        WHERE a.club_id = ?
        ORDER BY a.id DESC
        LIMIT 30
    ''', (club_id,)).fetchall()


    clubs = conn.execute('SELECT * FROM clubs').fetchall()  # Fetching all clubs
    conn.close()

    return render_template('announcements.html', club=club, announcements=club_announcements, clubs=clubs, current_club_id=club_id, user_pfp=user_pfp)

@app.route('/announcementsmobile.html/<int:club_id>', methods=['GET', 'POST'])
def AnnouncementMobile(club_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))
    user_pfp = session.get('user_pfp')
    conn = get_db_connection()
    club = conn.execute('SELECT * FROM clubs WHERE id = ?', (club_id,)).fetchone()
    if not club:
        conn.close()
        return 'Club not found', 404

    if request.method == 'POST':
        if 'announcement' in request.form:
            announcement = request.form['announcement']
            created_by = session.get('user_name')
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute('INSERT INTO announcements (club_id, announcement, created_by, created_at) VALUES (?, ?, ?, ?)', 
                         (club_id, announcement, created_by, created_at))
            conn.commit()

    # Fetch the latest 30 announcements along with the user's name and profile picture
    club_announcements = conn.execute('''
        SELECT a.announcement, a.created_at, u.user_name, u.user_pfp 
        FROM announcements a
        JOIN users u ON a.created_by = u.user_name
        WHERE a.club_id = ?
        ORDER BY a.id DESC
        LIMIT 30
    ''', (club_id,)).fetchall()


    clubs = conn.execute('SELECT * FROM clubs').fetchall()  # Fetching all clubs
    conn.close()

    return render_template('Announcementsmobile.html', club=club, announcements=club_announcements, clubs=clubs, current_club_id=club_id, user_pfp=user_pfp)


@app.route('/Buisness.html')  
def Business():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))
    return render_template('Business.html')

@app.route('/editEvent/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        event_date = request.form['event_date']
        event_time = request.form['event_time']
        event_location = request.form['event_location']
        
        conn.execute(
            'UPDATE events SET name = ?, description = ?, event_date = ?, event_time = ?, event_location = ? WHERE id = ?',
            (name, description, event_date, event_time,event_location, event_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('Events'))
    
    # Preload event details
    event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
    conn.close()
    if event:
        return render_template('edit_event.html', event=event)
    else:
        return "Event not found", 404

@app.route('/eventDetails/<int:event_id>', methods=['GET'])
def event_details(event_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Query the event by ID
    event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
    conn.close()

    # Check if the event exists
    if event:
        return render_template('eventDetails.html', event=event)
    else:
        # If no event found, redirect with error message
        return redirect(url_for('Events', notification='error'))


@app.route('/Events.html', methods=['GET'])
@app.route('/Events.html/<category>', methods=['GET'])
def Events(category=None):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Sanitize category value (remove special characters if necessary)
    if category:
        category = category.replace('<', '').replace('>', '')  # Remove special characters
        # Assuming `category` is not used in this context for the new events table
        events = conn.execute("SELECT * FROM events").fetchall()
    else:
        # Default to 'events' if no category is specified
        events = conn.execute("SELECT * FROM events").fetchall()

    # Debugging: Print retrieved events
    print(f"Retrieved events for category '{category}': {events}")

    user_email = session.get('user_email')
    registered_events = set()
    
    if user_email:
        user = conn.execute('SELECT user_id, user_role FROM users WHERE user_email = ?', (user_email,)).fetchone()
        if user:
            user_id = user['user_id']
            user_role = user['user_role']
            registrations = conn.execute('SELECT club_id FROM clublink WHERE user_id = ?', (user_id,)).fetchall()
            registered_events = {row['club_id'] for row in registrations}
        else:
            user_role = 'student'  # Default role if user not found

    events_with_status = []
    for event in events:
        event_dict = dict(event)
        event_dict['registered'] = event['id'] in registered_events
        event_dict['user_role'] = user_role
        events_with_status.append(event_dict)

    conn.close()
    return render_template('Events.html', events=events_with_status, category=category or 'Events', user_role=user_role)
@app.route('/deleteEvent/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Only allow admin users to delete events
    user_email = session.get('user_email')
    conn = get_db_connection()
    
    user = conn.execute('SELECT user_role FROM users WHERE user_email = ?', (user_email,)).fetchone()
    if user and user['user_role'] == 'admin':
        conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('Events'))  # Redirect back to the events page after deletion
    else:
        conn.close()
        return redirect(url_for('Events', notification='error'))  # Redirect with error notification if unauthorized
    
    
@app.route('/Eventsmobile.html', methods=['GET'])
@app.route('/Eventsmobile.html/<category>', methods=['GET'])
def Eventsmobile(category=None):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Sanitize category value (remove special characters if necessary)
    if category:
        category = category.replace('<', '').replace('>', '')  # Remove special characters
        # Assuming `category` is not used in this context for the new events table
        events = conn.execute("SELECT * FROM events").fetchall()
    else:
        # Default to 'events' if no category is specified
        events = conn.execute("SELECT * FROM events").fetchall()

    # Debugging: Print retrieved events
    print(f"Retrieved events for category '{category}': {events}")

    user_email = session.get('user_email')
    registered_events = set()
    
    if user_email:
        user = conn.execute('SELECT user_id, user_role FROM users WHERE user_email = ?', (user_email,)).fetchone()
        if user:
            user_id = user['user_id']
            user_role = user['user_role']
            registrations = conn.execute('SELECT club_id FROM clublink WHERE user_id = ?', (user_id,)).fetchall()
            registered_events = {row['club_id'] for row in registrations}
        else:
            user_role = 'student'  # Default role if user not found

    events_with_status = []
    for event in events:
        event_dict = dict(event)
        event_dict['registered'] = event['id'] in registered_events
        event_dict['user_role'] = user_role
        events_with_status.append(event_dict)
    user_pfp = session.get('user_pfp')  # Get the user profile picture URL

    conn.close()
    return render_template('EventsMobile.html', events=events_with_status, category=category or 'Events', user_role=user_role, user_pfp=user_pfp)
#i wanna die  - madheswaran kamal


@app.route('/Clubsmobile.html', methods=['GET'])
def Clubsmobile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))
    user_pfp = session.get('user_pfp')
    return render_template('clubsmobile.html', user_pfp=user_pfp)

@app.route('/get_events')
def get_events():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    events = conn.execute("SELECT name, event_date, event_time, id, description FROM events").fetchall()
    conn.close()

    events_list = []
    for event in events:
        event_date = event['event_date']
        event_time = event['event_time']
        print(event_time)

        event_dict = {
            'title': event['name'],
            'start': f"{event_date}T{event_time}",
            'description': event['description'],
            'id': event['id']
        }
        events_list.append(event_dict)

    return jsonify(events_list)
    
@app.route('/calendar')
def calendar():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('calendar.html')

@app.route('/calendarMob')
def calendarMob():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    user_pfp = session.get('user_pfp')
    return render_template('calendarMobile.html', user_pfp=user_pfp)

    
@app.route('/guidance')
def guidance():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('guidance.html')

# Route for the login page
@app.route('/login')
def login():
    loginv = True # IMPORTANT: Change this to True to enable login ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    if loginv == False:
        session['google_id'] = "123456789"
        session['name'] = "admin"
        session['logged_in'] = True
        session['user_email'] = "admin@example.com"
        session['user_pfp'] = "https://via.placeholder.com/150"
        session['user_role'] = "admin"
        name = session['name']
        email = session['user_email']
        pfp = session['user_pfp']
        

        conn = get_db_connection()

        existing_user = conn.execute('SELECT 1 FROM users WHERE user_email = ?', (email,)).fetchone()
        print(existing_user)
        if existing_user == None:
            conn.execute('INSERT INTO users (user_name, user_email, user_pfp) VALUES (?, ?, ?)',
                        (name, email, pfp))
            conn.commit()
            conn.close()
        return redirect(url_for('home'))
    next_page = request.args.get('next', '')
    return render_template('loginpage.html', next=next_page)


@app.route('/AdminPanel', methods=['POST', 'GET'])
def AdminPanel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if session['user_role'] != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()
    success_message = None

    if request.method == 'POST':
        if 'update_user_role' in request.form:
            email = request.form['name']

            query = """
            UPDATE users
            SET user_role = 'admin'
            WHERE user_email = ?
            """
            cursor.execute(query, (email,))
            conn.commit()

            success_message = "User role updated to admin successfully"

        if 'unupdate_user_role' in request.form:
            email = request.form['name']
            if email != 'vinod.vynavin@gmail.com' and email != 'saturnv24@gmail.com' and email != 'hbswitchboard@gmail.com':
                query = """
                UPDATE users
                SET user_role = 'student'
                WHERE user_email = ?
                """
                cursor.execute(query, (email,))
                conn.commit()

                success_message = "User role reverted to student successfully"
            else:
                #Rickroll the user if they try to change the role of the site devs
                #made by saturnv24
                return redirect("https://youtu.be/dQw4w9WgXcQ?si=uJmcwmAXokH5b0jc")

        elif 'update_clublink_role' in request.form:
            email = request.form['name']
            club_id = request.form.get('club')
            role = request.form.get('role')

            if club_id and role:
                user = cursor.execute('SELECT user_id FROM users WHERE user_email = ?', (email,)).fetchone()
                username = cursor.execute('SELECT user_name FROM users WHERE user_email = ?', (email,)).fetchone()

                if user:
                    user_id = user['user_id']
                    user_name1 = username['user_name']



                    if role == "owner":
                        cursor.execute('''UPDATE clubs SET created_by = ? WHERE id = ?''', (user_name1, club_id))
                        cursor.execute('''
                        UPDATE clublink
                        SET role = ?
                        WHERE user_id = ? AND club_id = ?
                    ''', ("admin", user_id, club_id))
                    else:
                        cursor.execute('''
                        UPDATE clublink
                        SET role = ?
                        WHERE user_id = ? AND club_id = ?
                    ''', (role, user_id, club_id))
                    


                    conn.commit()

                    success_message = "Role in clublink updated successfully"

    # Retrieve the clubs from the database to populate the dropdown
    clubs = cursor.execute('SELECT id, name FROM clubs').fetchall()

    return render_template('AdminPanel.html', success_message=success_message, clubs=clubs)



# Route to verify login credentials
@app.route('/verifyLogin', methods=['POST'])
def verifyLogin():
    correct_email = 'admin@example.com'
    correct_password = 'password123'

    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route('/credits')
def credits():
    return render_template('credits.html')
    
@app.route('/callback') 
def callback():
    try:
        # Fetch the OAuth 2.0 tokens using the authorization response
        flow.fetch_token(authorization_response=request.url)

        # Check if 'state' exists in the session and if it matches the 'state' from the request
        if 'state' not in session or session['state'] != request.args.get('state'):
            print("State does not match")
            return redirect(url_for("login"))

        credentials = flow.credentials
        request_session = requests.Session()
        cached_session = cachecontrol.CacheControl(request_session)
        token_request = google.auth.transport.requests.Request(session=cached_session)

        # Verify the ID token received from Google
        id_info = id_token.verify_oauth2_token(
            id_token=credentials.id_token, 
            request=token_request, 
            audience=CLIENT_ID, 
            clock_skew_in_seconds=10
        )
        
        # Store user information in the session
        session['google_id'] = id_info.get("sub")
        session['name'] = id_info.get("name")
        session['logged_in'] = True
        session['user_email'] = id_info.get("email")
        session['user_pfp'] = id_info.get("picture")

        name = session['name']
        email = session['user_email']
        pfp = session['user_pfp']

        conn = get_db_connection()

        # Check if the user already exists in the database
        existing_user = conn.execute('SELECT 1 FROM users WHERE user_email = ?', (email,)).fetchone()

        # Determine user role based on email
        if re.match(r'^[a-zA-Z].*@pdsb\.net$', email):
            session['user_role'] = "admin"
        elif re.search(r'pdsb\.net$', email):
            session['user_role'] = "student"
        elif email in ["vinod.vynavin@gmail.com", "saturnv24@gmail.com", "hbswitchboard@gmail.com"]:
            session['user_role'] = "admin"
        else:
            return render_template('acess.html')

        # If the user does not exist, insert them into the database
        if existing_user is None:
            user_role = session['user_role']
            conn.execute('INSERT INTO users (user_name, user_email, user_pfp, user_role) VALUES (?, ?, ?, ?)',
                        (name, email, pfp, user_role))
            conn.commit()

        conn.close()
        
        # Redirect to the home page after login
        return redirect(url_for('home'))
    except Exception as e:
        print(e)
        return render_template('error.html')


@app.route('/check_registration/<int:club_id>', methods=['GET'])
def check_registration(club_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))

    user_email = session.get('user_email')
    print(user_email)

    conn = get_db_connection()
    user = conn.execute('SELECT user_id FROM users WHERE user_email = ?', (user_email,)).fetchone()
    if user:
        user_id = user['user_id']
        registration = conn.execute('SELECT 1 FROM clublink WHERE club_id = ? AND user_id = ?', (club_id, user_id)).fetchone()
        registered = registration is not None
    else:
        registered = False

    conn.close()
    return {'registered': registered}

@app.route('/register_club', methods=['POST'])
def register_club():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))

    club_id = request.form.get('club_id')
    category = request.form.get('category', 'Tech')  # Get the category from the form, default to 'Tech'
    email = session['user_email']

    conn = get_db_connection()
    user = conn.execute('SELECT user_id, user_role FROM users WHERE user_email = ?', (email,)).fetchone()
    
    if user:
        user_id = user['user_id']
        user_role = user['user_role']
        
        admin_check = conn.execute('SELECT 1 FROM clublink WHERE club_id = ? AND user_id = ? AND role = "admin"', (club_id, user_id)).fetchone()

        if admin_check:
            flash('As an admin, you cannot unregister from your own club.')
            return redirect(url_for('tech', category=category, notification='admin_unreg'))
        else:
            existing_link = conn.execute('SELECT 1 FROM clublink WHERE club_id = ? AND user_id = ?', (club_id, user_id)).fetchone()
            if existing_link:
                conn.execute('DELETE FROM clublink WHERE club_id = ? AND user_id = ?', (club_id, user_id))
                conn.commit()
                return redirect(url_for('tech', category=category, notification='unregistered'))
            else:
                conn.execute('INSERT INTO clublink (club_id, user_id, role) VALUES (?, ?, ?)', (club_id, user_id, 'member'))
                conn.commit()
            return redirect(url_for('tech', category=category, notification='registered'))
    else:
        return redirect(url_for('tech', category=category, notification='error'))
    
@app.route('/register_club1', methods=['POST'])
def register_club1():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))

    club_id = request.form.get('club_id')
    email = session['user_email']

    conn = get_db_connection()
    user = conn.execute('SELECT user_id, user_role FROM users WHERE user_email = ?', (email,)).fetchone()
    
    if user:
        user_id = user['user_id']
        user_role = user['user_role']
        
        admin_check = conn.execute('SELECT 1 FROM clublink WHERE club_id = ? AND user_id = ? AND role = "admin"', (club_id, user_id)).fetchone()

        if admin_check:
            flash('As an admin, you cannot unregister from your own club.')
            return redirect(url_for('tech', notification='admin_unreg'))
        else:
            existing_link = conn.execute('SELECT 1 FROM clublink WHERE club_id = ? AND user_id = ?', (club_id, user_id)).fetchone()
            if existing_link:
                conn.execute('DELETE FROM clublink WHERE club_id = ? AND user_id = ?', (club_id, user_id))
                conn.commit()
                return redirect(url_for('tech', notification='unregistered'))
            else:
                conn.execute('INSERT INTO clublink (club_id, user_id, role) VALUES (?, ?, ?)', (club_id, user_id, 'member'))
                conn.commit()
            return redirect(url_for('tech', notification='registered'))
    else:
        return redirect(url_for('tech', notification='error'))
    

@app.route('/register_club2', methods=['POST'])
def register_club2():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))

    club_id = request.form.get('club_id')
    category = request.form.get('category', 'Tech')  # Get the category from the form, default to 'Tech'
    email = session['user_email']

    conn = get_db_connection()
    user = conn.execute('SELECT user_id, user_role FROM users WHERE user_email = ?', (email,)).fetchone()
    
    if user:
        user_id = user['user_id']
        user_role = user['user_role']
        
        admin_check = conn.execute('SELECT 1 FROM clublink WHERE club_id = ? AND user_id = ? AND role = "admin"', (club_id, user_id)).fetchone()

        if admin_check:
            flash('As an admin, you cannot unregister from your own club.')
            return redirect(url_for('myclubs', category=category, notification='admin_unreg'))
        else:
            existing_link = conn.execute('SELECT 1 FROM clublink WHERE club_id = ? AND user_id = ?', (club_id, user_id)).fetchone()
            if existing_link:
                conn.execute('DELETE FROM clublink WHERE club_id = ? AND user_id = ?', (club_id, user_id))
                conn.commit()
                return redirect(url_for('myclubs', category=category, notification='unregistered'))
            else:
                conn.execute('INSERT INTO clublink (club_id, user_id, role) VALUES (?, ?, ?)', (club_id, user_id, 'member'))
                conn.commit()
            return redirect(url_for('myclubs', category=category, notification='registered'))
    else:
        return redirect(url_for('myclubs', category=category, notification='error'))





@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    return redirect(url_for('login'))


import time

@app.route('/addClub', methods=['GET', 'POST'])
def addClub():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))
    if session['user_role'] != 'admin':
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        file = request.files['image']

        if file and allowed_file(file.filename):
            # Generate a unique filename using the club name and current timestamp
            filename = secure_filename(f"{name}_{int(time.time())}.{file.filename.rsplit('.', 1)[1].lower()}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            resize_image(filepath)  # Resize the image
            image_url = 'uploads/' + filename
        else:
            flash('Invalid file format. Allowed formats are png, jpg, jpeg, gif.')
            return redirect(request.url)

        user_name = session['name']

        conn = get_db_connection()
        try:
            # Insert the new club
            cursor = conn.cursor()
            cursor.execute('INSERT INTO clubs (name, description, category, image_url, created_by) VALUES (?, ?, ?, ?, ?)',
                        (name, description, category, image_url, user_name))
            conn.commit()

            # Get the ID of the newly inserted club
            club_id = cursor.lastrowid

            # Get the user ID
            email = session['user_email']
            user = conn.execute('SELECT user_id FROM users WHERE user_email = ?', (email,)).fetchone()
            if user:
                user_id = user[0]
            else:
                user_id = None

            # Insert into clublink table
            cursor.execute('INSERT INTO clublink (club_id, user_id, role) VALUES (?, ?, ?)',
                        (club_id, user_id, "admin"))
            conn.commit()
            conn.close()

            return redirect(url_for('allClubs'))
        except Exception as e:
            return render_template('error.html')

    return render_template('addClub.html')

@app.route('/addEvents.html', methods=['GET', 'POST'])
def addEvents():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))
    if session['user_role'] != 'admin':
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        event_date = request.form['event_date']
        event_time = request.form['event_time']
        event_location = request.form['event_location']
        file = request.files['image']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            resize_image(filepath)  # Resize the image
            image_url = 'uploads/' + filename
        else:
            flash('Invalid file format. Allowed formats are png, jpg, jpeg, gif.')
            return redirect(request.url)

        user_name = session['name']

        conn = get_db_connection()

        # Insert the new event
        event_year = 'already assigned'
        cursor = conn.cursor()
        cursor.execute('INSERT INTO events (name, description, event_date, event_time, event_year, image_url, created_by, event_location) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                       (name, description, event_date, event_time, event_year, image_url, user_name, event_location))
        conn.commit()
        print("Event added", name, description, event_date, event_time, event_year, image_url, user_name, event_location)
        # Get the ID of the newly inserted event
        event_id = cursor.lastrowid

        # Get the user ID
        email = session['user_email']
        user = conn.execute('SELECT user_id FROM users WHERE user_email = ?', (email,)).fetchone()
        if user:
            user_id = user[0]
        else:
            user_id = None

        # Insert into clublink table
        cursor.execute('INSERT INTO clublink (club_id, user_id, role) VALUES (?, ?, ?)',
                       (event_id, user_id, "admin"))
        conn.commit()
        conn.close()

        return redirect(url_for('home'))

    return render_template('addEvents.html')



@app.route('/manageClub/<int:club_id>', methods=['GET', 'POST'])
def manageClub(club_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user_id = conn.execute('SELECT user_id FROM users WHERE user_email = ?', (session['user_email'],)).fetchone()['user_id']
    
    # Check if the user is an admin of the specific club
    clubrole = conn.execute('''
        SELECT role 
        FROM clublink 
        WHERE user_id = ? AND club_id = ? AND role = 'admin'
    ''', (user_id, club_id)).fetchone()

    # Ensure the user is either a site-wide admin or an admin of the specific club
    if not (session['user_role'] == 'admin' or clubrole is not None):
        return redirect(url_for('home'))

    # Fetch club details and ensure the club exists
    club = conn.execute('SELECT * FROM clubs WHERE id = ?', (club_id,)).fetchone()
    if not club:
        conn.close()
        return 'Club not found', 404
    
    created_by = session['name']
    user_pfp = session['user_pfp']  
    created_at = datetime.now().strftime("Posted at: %m/%d/%Y, %I:%M%p").replace(" 0", " ").replace("AM", "AM").replace("PM", "PM")

    if request.method == 'POST':
        if 'announcement' in request.form:
            announcement = request.form['announcement']
            conn.execute('INSERT INTO announcements (club_id, announcement, created_by, created_at) VALUES (?, ?, ?, ?)',
                         (club_id, announcement, created_by, created_at))
            conn.commit()
        elif 'delete_announcement_id' in request.form:
            delete_announcement_id = request.form['delete_announcement_id']
            conn.execute(
                'DELETE FROM announcements WHERE id = ? AND club_id = ?',
                (delete_announcement_id, club_id)
            )
            conn.commit()
        elif 'edit_announcement_id' in request.form:
            edit_announcement_id = request.form['edit_announcement_id']
            edited_announcement = request.form['edited_announcement']
            conn.execute(
                'UPDATE announcements SET announcement = ? WHERE id = ? AND club_id = ?',
                (edited_announcement, edit_announcement_id, club_id)
            )
            conn.commit()

    # Fetch club announcements and all clubs
    club_announcements = conn.execute('''
        SELECT a.id, a.announcement, a.created_at, u.user_name, u.user_pfp 
        FROM announcements a
        JOIN users u ON a.created_by = u.user_name
        WHERE a.club_id = ?
        ORDER BY a.id DESC
        LIMIT 30
    ''', (club_id,)).fetchall()
    
    # Fetch club members
    members = conn.execute('''
        SELECT u.user_name, u.user_email, u.user_pfp
        FROM clublink cl
        JOIN users u ON cl.user_id = u.user_id
        WHERE cl.club_id = ?
    ''', (club_id,)).fetchall()
    
    clubs = conn.execute('SELECT * FROM clubs').fetchall()  
    conn.close()

    return render_template('manageClub.html', club=club, announcements=club_announcements, clubs=clubs, 
                           current_club_id=club_id, user_pfp=user_pfp, members=members)
@app.route('/members/<int:club_id>', methods=['GET', 'POST'])
@app.route('/members/<int:club_id>', methods=['GET', 'POST'])
def members(club_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    user_id = conn.execute('SELECT user_id FROM users WHERE user_email = ?', (session['user_email'],)).fetchone()['user_id']
    
    # Check if the user is an admin of the specific club
    clubrole = conn.execute('''
        SELECT role 
        FROM clublink 
        WHERE user_id = ? AND club_id = ? AND role = 'admin'
    ''', (user_id, club_id)).fetchone()

    # Ensure the user is either a site-wide admin or an admin of the specific club
    if not (session['user_role'] == 'admin' or clubrole is not None):
        return redirect(url_for('home'))

    # Fetch club details and ensure the club exists
    club = conn.execute('SELECT * FROM clubs WHERE id = ?', (club_id,)).fetchone()
    if not club:
        conn.close()
        return 'Club not found', 404
    
    created_by = session['name']
    user_pfp = session['user_pfp']  
    created_at = datetime.now().strftime("Posted at: %m/%d/%Y, %I:%M%p").replace(" 0", " ").replace("AM", "AM").replace("PM", "PM")

    if request.method == 'POST':
        if 'announcement' in request.form:
            announcement = request.form['announcement']
            conn.execute('INSERT INTO announcements (club_id, announcement, created_by, created_at) VALUES (?, ?, ?, ?)',
                         (club_id, announcement, created_by, created_at))
            conn.commit()
        elif 'delete_announcement_id' in request.form:
            delete_announcement_id = request.form['delete_announcement_id']
            conn.execute(
                'DELETE FROM announcements WHERE id = ? AND club_id = ?',
                (delete_announcement_id, club_id)
            )
            conn.commit()
        elif 'edit_announcement_id' in request.form:
            edit_announcement_id = request.form['edit_announcement_id']
            edited_announcement = request.form['edited_announcement']
            conn.execute(
                'UPDATE announcements SET announcement = ? WHERE id = ? AND club_id = ?',
                (edited_announcement, edit_announcement_id, club_id)
            )
            conn.commit()

    # Fetch club announcements and all clubs
    club_announcements = conn.execute('''
        SELECT a.id, a.announcement, a.created_at, u.user_name, u.user_pfp 
        FROM announcements a
        JOIN users u ON a.created_by = u.user_name
        WHERE a.club_id = ?
        ORDER BY a.id DESC
        LIMIT 30
    ''', (club_id,)).fetchall()
    
    # Fetch club members
    members = conn.execute('''
        SELECT u.user_name, u.user_email, u.user_pfp
        FROM clublink cl
        JOIN users u ON cl.user_id = u.user_id
        WHERE cl.club_id = ?
    ''', (club_id,)).fetchall()

    # Calculate the number of members
    member_count = len(members)
    
    clubs = conn.execute('SELECT * FROM clubs').fetchall()  
    conn.close()

    return render_template('members.html', club=club, announcements=club_announcements, clubs=clubs, 
                           current_club_id=club_id, user_pfp=user_pfp, members=members, member_count=member_count)


import os
import shutil
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
# Initialize the scheduler
scheduler = BackgroundScheduler()

def delete_expired_events():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current date and time
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Delete events where the event_date and event_time are less than or equal to the current date and time
    cursor.execute('DELETE FROM events WHERE datetime(event_date || " " || event_time) <= ?', (now,))
    conn.commit()
    conn.close()
    print('Expired events deleted')

def backup_database():
    # Create a 'Backups' folder if it doesn't exist
    if not os.path.exists('Backups'):
        os.makedirs('Backups')

    # Get current date for backup filename
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_filename = f"Backups/database_backup_{now}.db"

    # Copy the database file to the 'Backups' folder
    shutil.copyfile('database.db', backup_filename)
    print(f'Backup created: {backup_filename}')

    # Delete backups older than 3 days
    three_days_ago = datetime.now() - timedelta(days=3)

    for backup_file in os.listdir('Backups'):
        backup_path = os.path.join('Backups', backup_file)
        
        # Get the file creation time and compare
        file_creation_time = datetime.fromtimestamp(os.path.getctime(backup_path))
        if file_creation_time < three_days_ago:
            os.remove(backup_path)
            print(f'Old backup deleted: {backup_path}')

scheduler.add_job(delete_expired_events, 'interval', hours=24)
scheduler.add_job(backup_database, 'interval', hours=24)
scheduler.start()
@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('error.html'), 404

@app.route('/techMob/<category>', methods=['GET'])
def techMob(category=None):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('google_id'):
        return redirect(url_for('login'))



    conn = get_db_connection()

    # Sanitize category value (remove special characters if necessary)
    if category:
        category = category.replace('<', '').replace('>', '')  # Remove special characters
        clubs = conn.execute("SELECT * FROM clubs WHERE category = ?", (category,)).fetchall()
    else:
        clubs = conn.execute("SELECT * FROM clubs WHERE category = 'Tech'").fetchall()

    user_email = session.get('user_email')
    registered_clubs = set()
    user_role = 'student'  # Default role

    if user_email:
        user = conn.execute('SELECT user_id, user_role FROM users WHERE user_email = ?', (user_email,)).fetchone()
        if user:
            user_id = user['user_id']
            user_role = user['user_role']
            registrations = conn.execute('SELECT club_id FROM clublink WHERE user_id = ?', (user_id,)).fetchall()
            registered_clubs = {row['club_id'] for row in registrations}

    clubs_with_status = []
    for club in clubs:
        club_dict = dict(club)
        club_dict['registered'] = club['id'] in registered_clubs
        club_dict['user_role'] = user_role
        clubs_with_status.append(club_dict)

    conn.close()
    user_pfp = session.get('user_pfp')
    return render_template('techMobile.html', tech_clubs=clubs_with_status, category=category or 'Tech', user_role=user_role, user_pfp=user_pfp)

if __name__ == '__main__':
    app.run(port=5001, debug=True)
