from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Replace with a more secure key

# MongoDB setup (update your connection string as needed)
client = MongoClient('mongodb+srv://kumawatr:JhvogRcEEo10IHyI@cluster9.2bjhi.mongodb.net/')
db = client['tutouring-platform']
students_collection = db['students']
tutors_collection = db['tutors']
sessions_collection = db['sessions']  # Collection for session management
booking_confirmation_collection = db['booking_confirmation']  # Collection for booking confirmations

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register/student1', methods=['POST'])
def register_student1():
    if request.method == 'POST':
        full_name = request.json['full_name']
        email = request.json['email']
        password = request.json['password']
        
        # Check if the user already exists
        if students_collection.find_one({'email': email}):
            return "User already exists. Please choose a different email."
        
        # Store user information
        students_collection.insert_one({'full_name': full_name, 'email': email, 'password': password})
        return redirect(url_for('login'))  # Redirect to login after registration
    return render_template('register.html')

# Student Registration
@app.route('/register/student', methods=['POST'])
def register_student():
    data = request.json
    if students_collection.find_one({"email": data['email']}):
        return jsonify({"message": "Email already registered."}), 400
    hashed_password = generate_password_hash(data['password'])
    student_data = {
        "full_name": data['full_name'],
        "email": data['email'],
        "password": hashed_password,
        "registration_date": datetime.now(),
        "session_history": []
    }
    students_collection.insert_one(student_data)
    return redirect(url_for('login'))  # Redirect to login after registration

# Student Login
@app.route('/login/student', methods=['POST'])
def login_student():
    data = request.json
    student = students_collection.find_one({"email": data['email']})
    if student and check_password_hash(student['password'], data['password']):
        session['student_id'] = str(student['_id'])
        session['username'] = student['full_name']
        return redirect(url_for('dashboard'))  # Redirect to dashboard on successful login
    else:
        return jsonify({"message": "Invalid credentials."}), 401

# View Tutors
@app.route('/tutors', methods=['GET'])
def view_tutors():
    tutors = list(tutors_collection.find())
    for tutor in tutors:
        tutor['_id'] = str(tutor['_id'])
    return jsonify(tutors), 200

# Book Confirm
@app.route('/book/confirm', methods=['POST'])
def booking_confirmation():
    data = request.json
    student_id = session.get('student_id')
    if not student_id:
        return jsonify({"message": "User not logged in."}), 401
    
    session_data = {
        "tutor_id": data['tutor_id'],
        "tutor_name": data['tutor_name'],
        "tutor_subject": data['tutor_subject'],
        "scheduled_time": data['scheduled_time'],
        "status": "booked",
        "booking_date": datetime.now()
    }

    # Check for existing sessions to avoid double booking
    existing_session = sessions_collection.find_one({
        "tutor_id": data['tutor_id'],
        "scheduled_time": data['scheduled_time']
    })

    if existing_session:
        return jsonify({"message": "This session time is already booked."}), 400

    # return render_template('booking_confirmation.html', session_data=session_data)
    return jsonify(session_data)

# Book Session
@app.route('/book/session', methods=['POST'])
def book_session():
    data = request.json
    student_id = session.get('student_id')
    if not student_id:
        return jsonify({"message": "User not logged in."}), 401

    session_data = {
        "tutor_id": data['tutor_id'],
        "tutor_name": data['tutor_name'],
        "tutor_subject": data['tutor_subject'],
        "scheduled_time": data['scheduled_time'],
        "status": "booked",
        "booking_date": datetime.now()
    }

    # Check for existing sessions to avoid double booking
    existing_session = sessions_collection.find_one({
        "tutor_id": data['tutor_id'],
        "scheduled_time": data['scheduled_time']
    })

    if existing_session:
        return jsonify({"message": "This session time is already booked."}), 400

    students_collection.update_one(
        {"_id": ObjectId(student_id)},
        {"$push": {"session_history": session_data}}
    )
    sessions_collection.insert_one(session_data)  # Store booked session in sessions collection
    return jsonify({"message": "Session booked successfully!"}), 201
    
# # View Session History
# @app.route('/students/<student_id>/sessions', methods=['GET'])
# def view_session_history(student_id):
#     student = students_collection.find_one({"_id": ObjectId(student_id)})
#     if student:
#         return render_template('booking_confirmation.html', session_history=student['session_history'])
#         # return redirect(url_for('booking_confirmation', student_id=student_id))
#         # return jsonify(student['session_history']), 200
#     return jsonify({"message": "Student not found."}), 404

# Tutor Registration
@app.route('/register/tutor', methods=['POST'])
def register_tutor():
    data = request.json
    if tutors_collection.find_one({"email": data['email']}):
        return jsonify({"message": "Email already registered."}), 400
    hashed_password = generate_password_hash(data['password'])
    tutor_data = {
        "full_name": data['full_name'],
        "email": data['email'],
        "password": hashed_password,
        "registration_date": datetime.now(),
        "availability": []
    }
    tutors_collection.insert_one(tutor_data)
    return jsonify({"message": "Tutor registered successfully!"}), 201

# Tutor Login
@app.route('/login/tutor', methods=['POST'])
def login_tutor():
    data = request.json
    tutor = tutors_collection.find_one({"email": data['email']})
    if tutor and check_password_hash(tutor['password'], data['password']):
        session['tutor_id'] = str(tutor['_id'])
        return jsonify({"message": "Login successful!"}), 200
    else:
        return jsonify({"message": "Invalid credentials."}), 401

# View Students
@app.route('/tutors/<tutor_id>/students', methods=['GET'])
def view_students(tutor_id):
    # Logic to retrieve students assigned to the tutor
    return jsonify([]), 200  # Replace with actual student data

# Manage Sessions
@app.route('/tutors/<tutor_id>/manage_sessions', methods=['POST'])
def manage_sessions(tutor_id):
    data = request.json
    # Logic to manage tutor's sessions (update availability)
    return jsonify({"message": "Sessions managed successfully!"}), 200

# Dashboard Route
@app.route('/dashboard')
def dashboard():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    tutors = list(tutors_collection.find())
    for tutor in tutors:
        tutor['_id'] = str(tutor['_id'])

    return render_template('dashboard.html', username=session['username'], tutors=tutors)

# View Session History
@app.route('/sessions', methods=['GET'])
def sessions():
    student_id = session['student_id']
    if student_id:
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        if student:
            return render_template('booked_sessions.html', sessions=student['session_history'])
            # return redirect(url_for('booking_confirmation', student_id=student_id))
            # return jsonify(student['session_history']), 200
    return jsonify({"message": "Student not found."}), 404

# Add routes for register and login pages
@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

# Add routes for contact, terms, and privacy pages
@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


if __name__ == '__main__':
    app.run(port=5059, debug=True)
