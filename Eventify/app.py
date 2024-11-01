from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify
import json
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# File paths
USERS_FILE = 'data/users.json'
ACTIVITIES_FILE = 'data/activities.json'
SIGNUPS_FILE = 'data/signups.json'
ATTENDANCE_FILE = 'data/attendance.json'
FEEDBACK_FILE = 'data/feedback.json'

# Helper functions to read and write JSON files
def read_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def write_json(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Decorators for role-based access
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if g.current_user['role'] not in roles:  # Change to ['role']
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return wrapped
    return wrapper

# Initialize admin account if it doesn't exist
def init_admin():
    users = read_json(USERS_FILE)
    admin_exists = any(u['role'] == 'Admin' for u in users)
    if not admin_exists:
        admin_user = {
            'username': 'admin',
            'password': generate_password_hash('admin123'),
            'role': 'Admin',
            'name': 'Administrator',
            'description': '',
            'grade': ''
        }
        users.append(admin_user)
        write_json(USERS_FILE, users)
init_admin()

# Context processor to make current_user available in templates
@app.before_request
def before_request():
    if 'username' in session:
        users = read_json(USERS_FILE)
        g.current_user = next((u for u in users if u['username'] == session['username']), None)
    else:
        g.current_user = None

app.jinja_env.globals.update(current_user=lambda: g.current_user)

# Routes
@app.route('/')
def home():
    return render_template('home.html', hide_content=False)

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        if 'login' in request.form:
            # login logic
            username = request.form['username']
            password = request.form['password']
            # ... verification logic ...
        elif 'register' in request.form:
            # register logic
            username = request.form['username']
            password = request.form['password']
            name = request.form['name']
            description = request.form['description']
            grade = request.form['grade']
            # ... register logic ...
    return render_template('auth.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/manage_account', methods=['GET', 'POST'])
@login_required
def manage_account():
    users = read_json(USERS_FILE)
    user = next((u for u in users if u['username'] == session['username']), None)
    if request.method == 'POST':
        user['name'] = request.form['name']
        user['description'] = request.form['description']
        user['grade'] = request.form['grade']
        write_json(USERS_FILE, users)
        flash('Account details updated!', 'success')
        return redirect(url_for('manage_account'))
    return render_template('manage_account.html', user=user)

@app.route('/activities')
@login_required
def activities():
    activities = read_json(ACTIVITIES_FILE)
    signups = read_json(SIGNUPS_FILE)
    attendance = read_json(ATTENDANCE_FILE)
    
    # Get current user's signup status
    user_signups = [signup['activity_id'] for signup in signups if signup['username'] == g.current_user['username']]
    
    # Add 'signed_up' and 'attendance_count' fields to each activity
    for activity in activities:
        activity['signed_up'] = activity['id'] in user_signups
        activity['attendance_count'] = len([a for a in attendance if a['activity_id'] == activity['id'] and a['status'] == 'Present'])
    
    print("Activities with attendance count:", activities)  # 添加调试输出
    
    return render_template('activities.html', activities=activities)

@app.route('/my_attendance')
@login_required
def my_attendance():
    attendance = read_json(ATTENDANCE_FILE)
    activities = read_json(ACTIVITIES_FILE)
    user_attendance = []
    for att in attendance:
        if att['username'] == g.current_user['username']:
            activity = next((a for a in activities if a['id'] == att['activity_id']), None)
            if activity:
                user_attendance.append({
                    'activity_name': activity['name'],
                    'date': att['date'],
                    'status': att['status']
                })
    return render_template('my_attendance.html', attendance=user_attendance)

@app.route('/api/data')
def get_data():
    # Return the data you want to display in the frontend
    data = [
        {"name": "Activity 1", "value": "Description 1"},
        {"name": "Activity 2", "value": "Description 2"},
        # ... more data
    ]
    return jsonify(data)

@app.route('/api/data', methods=['POST'])
def add_data():
    new_data = request.json
    # Add logic to handle adding new data
    # For example, add new data to activities.json file
    activities = read_json(ACTIVITIES_FILE)
    new_id = max([a['id'] for a in activities], default=0) + 1
    activities.append({
        'id': new_id,
        'name': new_data['name'],
        'description': new_data['value']
    })
    write_json(ACTIVITIES_FILE, activities)
    return jsonify({"success": True, "message": "Data added successfully"})

@app.route('/activities/<int:activity_id>', methods=['GET', 'POST'])
@login_required
def activity(activity_id):
    activities = read_json(ACTIVITIES_FILE)
    activity = next((a for a in activities if a['id'] == activity_id), None)
    if not activity:
        flash('Activity not found.', 'danger')
        return redirect(url_for('activities'))
    if request.method == 'POST':
        signups = read_json(SIGNUPS_FILE)
        # Check for overlapping activities (simplified example)
        if any(s['activity_id'] == activity_id and s['username'] == session['username'] for s in signups):
            flash('You have already signed up for this activity.', 'warning')
        else:
            signups.append({'username': session['username'], 'activity_id': activity_id})
            write_json(SIGNUPS_FILE, signups)
            flash('You have signed up for the activity!', 'success')
        return redirect(url_for('activities'))
    return render_template('activity.html', activity=activity)

@app.route('/create_activity', methods=['GET', 'POST'])
@login_required
@roles_required('Teacher', 'Admin')
def create_activity():
    if request.method == 'POST':
        # Handle logic for creating an activity
        pass
    return render_template('create_activity.html')

@app.route('/manage_activities')
@login_required
@roles_required('Teacher', 'Admin')
def manage_activities():
    activities = read_json(ACTIVITIES_FILE)
    return render_template('manage_activities.html', activities=activities)

@app.route('/attendance')
@login_required
def attendance():
    users = read_json(USERS_FILE)
    current_user = next((u for u in users if u['username'] == session['username']), None)
    activities = read_json(ACTIVITIES_FILE)
    activity_dict = {activity['id']: activity for activity in activities}
    if current_user['role'] == 'Student':
        signups = read_json(SIGNUPS_FILE)
        user_activities = [s['activity_id'] for s in signups if s['username'] == session['username']]
        user_activity_details = [activity_dict[a_id] for a_id in user_activities]
        attendance = read_json(ATTENDANCE_FILE)
        user_attendance = [att for att in attendance if att['username'] == session['username']]
        attendance_status = {att['activity_id']: att['status'] for att in user_attendance}
        return render_template('attendance.html', activities=user_activity_details, attendance_status=attendance_status)
    else:
        # For Teacher and Admin to view activities
        activities = read_json(ACTIVITIES_FILE)
        return render_template('attendance_overview.html', activities=activities)

@app.route('/attendance/overview')
@login_required
@roles_required('Teacher', 'Admin')
def attendance_overview():
    activities = read_json(ACTIVITIES_FILE)
    # Add logic to calculate attendance rate
    return render_template('attendance_overview.html', activities=activities)

@app.route('/attendance/activity/<int:activity_id>')
@login_required
@roles_required('Teacher', 'Admin')
def activity_attendance(activity_id):
    activities = read_json(ACTIVITIES_FILE)
    activity = next((a for a in activities if a['id'] == activity_id), None)
    if not activity:
        flash('Activity not found.', 'danger')
        return redirect(url_for('attendance'))

    attendance = read_json(ATTENDANCE_FILE)
    signups = read_json(SIGNUPS_FILE)
    users = read_json(USERS_FILE)

    # Students who signed up for the activity
    signed_up_users = [s['username'] for s in signups if s['activity_id'] == activity_id]

    # Prepare data for attendance table
    student_attendance = []
    for username in signed_up_users:
        user = next((u for u in users if u['username'] == username), None)
        att_record = next((att for att in attendance if att['username'] == username and att['activity_id'] == activity_id), None)
        status = att_record['status'] if att_record else 'Not Marked'
        student_attendance.append({
            'username': username,
            'name': user['name'] if user else 'Unknown',
            'status': status
        })

    return render_template(
        'activity_attendance.html',
        activity=activity,
        student_attendance=student_attendance
    )

@app.route('/mark_attendance', methods=['GET', 'POST'])
@login_required
@roles_required('Teacher', 'Admin')
def mark_attendance():
    if request.method == 'POST':
        activity_id = request.form['activity_id']
        attendance = read_json(ATTENDANCE_FILE)
        
        for key, value in request.form.items():
            if key.startswith('attendance_'):
                student_id = int(key.split('_')[1])
                status = value
                attendance_record = {
                    'activity_id': int(activity_id),
                    'student_id': student_id,
                    'status': status,
                    'date': datetime.now().strftime('%Y-%m-%d')
                }
                attendance.append(attendance_record)
        
        write_json(ATTENDANCE_FILE, attendance)
        flash('Attendance marked successfully', 'success')
        return redirect(url_for('mark_attendance'))
    
    activities = read_json(ACTIVITIES_FILE)
    return render_template('mark_attendance.html', activities=activities)

@app.route('/get_activity_students/<int:activity_id>')
@login_required
@roles_required('Teacher', 'Admin')
def get_activity_students(activity_id):
    signups = read_json(SIGNUPS_FILE)
    users = read_json(USERS_FILE)
    
    activity_signups = [s for s in signups if s['activity_id'] == activity_id]
    students = [{'id': u['id'], 'name': u['name']} for u in users if u['role'] == 'Student' and any(s['username'] == u['username'] for s in activity_signups)]
    
    return jsonify({'students': students})

@app.route('/feedback')
def feedback():
    feedbacks = read_json(FEEDBACK_FILE)
    activities = read_json(ACTIVITIES_FILE)
    
    # Add activity name to each feedback
    for feedback in feedbacks:
        activity = next((a for a in activities if a['id'] == feedback['activity_id']), None)
        if activity:
            feedback['activity_name'] = activity['name']
    
    user_activities = []
    if g.current_user and g.current_user['role'] == 'Student':
        signups = read_json(SIGNUPS_FILE)
        user_signups = [s for s in signups if s['username'] == g.current_user['username']]
        for signup in user_signups:
            activity = next((a for a in activities if a['id'] == signup['activity_id']), None)
            if activity:
                activity['has_feedback'] = any(f['username'] == g.current_user['username'] and f['activity_id'] == activity['id'] for f in feedbacks)
                user_activities.append(activity)
    
    return render_template('feedback.html', feedbacks=feedbacks, user_activities=user_activities)

@app.route('/submit_feedback/<int:activity_id>', methods=['POST'])
@login_required
def submit_feedback(activity_id):
    data = request.json
    feedback = read_json(FEEDBACK_FILE)
    new_feedback = {
        'username': g.current_user['username'],
        'activity_id': activity_id,
        'rating': data['rating'],
        'comments': data['comments'],
        'timestamp': datetime.now().isoformat()
    }
    feedback.append(new_feedback)
    write_json(FEEDBACK_FILE, feedback)
    return jsonify({"success": True, "message": "Feedback submitted successfully"})

@app.route('/dashboard')
@login_required
@roles_required('Teacher', 'Admin')
def dashboard():
    # Calculate dashboard statistics
    stats = {
        'total_activities': len(read_json(ACTIVITIES_FILE)),
        'total_users': len(read_json(USERS_FILE)),
        'total_attendance': len(read_json(ATTENDANCE_FILE)),
        'total_feedback': len(read_json(FEEDBACK_FILE))
    }
    return render_template('dashboard.html', stats=stats)

@app.route('/manage_users')
@login_required
@roles_required('Admin')
def manage_users():
    users = read_json(USERS_FILE)
    return render_template('manage_users.html', users=users)

@app.route('/system_settings')
@login_required
@roles_required('Admin')
def system_settings():
    # Add system settings logic here
    return render_template('system_settings.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = read_json(USERS_FILE)
        user = next((user for user in users if user['username'] == username), None)
        
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'warning')
    
    return render_template('auth.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        name = request.form['name']
        
        users = read_json(USERS_FILE)
        if any(user['username'] == username for user in users):
            flash('Username already exists', 'warning')
        elif any(user['email'] == email for user in users):
            flash('Email already in use', 'warning')
        else:
            hashed_password = generate_password_hash(password)
            new_user = {
                'username': username,
                'password': hashed_password,
                'email': email,
                'name': name,
                'role': 'Student'  # Default role
            }
            users.append(new_user)
            write_json(USERS_FILE, users)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    
    return render_template('auth.html')

@app.route('/signup/<int:activity_id>', methods=['POST'])
@login_required
def signup_activity(activity_id):
    signups = read_json(SIGNUPS_FILE)
    activities = read_json(ACTIVITIES_FILE)
    
    # Check if activity exists
    activity = next((a for a in activities if a['id'] == activity_id), None)
    if not activity:
        return jsonify({"success": False, "message": "Activity not found."}), 404
    
    # Check if user has already signed up
    if any(signup['username'] == g.current_user['username'] and signup['activity_id'] == activity_id for signup in signups):
        return jsonify({"success": False, "message": "You have already signed up for this activity."}), 400
    
    # Add new signup record
    new_signup = {
        'username': g.current_user['username'],
        'activity_id': activity_id,
        'signup_date': datetime.now().isoformat()
    }
    signups.append(new_signup)
    write_json(SIGNUPS_FILE, signups)
    
    print(f"User {g.current_user['username']} signed up for activity {activity_id}")  # Add debugging output
    
    return jsonify({"success": True, "message": "You have successfully signed up for the activity."})

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    # Implement logic to change password
    return render_template('change_password.html')

@app.route('/edit_activity/<int:activity_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Teacher', 'Admin')
def edit_activity(activity_id):
    activities = read_json(ACTIVITIES_FILE)
    activity = next((a for a in activities if a['id'] == activity_id), None)
    if not activity:
        flash('Activity not found.', 'error')
        return redirect(url_for('manage_activities'))

    if request.method == 'POST':
        # Update activity information
        activity['name'] = request.form['name']
        activity['description'] = request.form['description']
        activity['date'] = request.form['date']
        activity['time'] = request.form['time']
        activity['location'] = request.form['location']
        activity['max_participants'] = int(request.form['max_participants'])
        
        write_json(ACTIVITIES_FILE, activities)
        flash('Activity updated successfully!', 'success')
        return redirect(url_for('manage_activities'))

    return render_template('edit_activity.html', activity=activity)

# Run this code when the app starts
if not os.path.exists(USERS_FILE):
    test_user = {
        'username': 'test',
        'password': generate_password_hash('test'),
        'role': 'Student',
        'name': 'Test User',
        'email': 'test@example.com'
    }
    write_json(USERS_FILE, [test_user])

if not os.path.exists(ATTENDANCE_FILE):
    test_attendance = [
        {
            "username": "test_user",
            "activity_id": 1,
            "status": "Present",
            "date": "2023-05-01"
        }
    ]
    write_json(ATTENDANCE_FILE, test_attendance)

if __name__ == '__main__':
    app.run(debug=True)
