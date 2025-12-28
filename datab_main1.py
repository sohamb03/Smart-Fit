from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from squats import generate_frames_squat  # Import the generate_frames function from squats.py
from shoulder_raises import generate_frames_shoulder # Import the generate_frames function from shoulder_raises.py
from shoulder_raises_feedback import shoulder_feedback_bp
from lunges import generate_frames_lunges # Import the generate_frames function from lunges.py
from tricep_pushback import generate_frames_tricep, reset_tricep
from bicep_curls import generate_frames_bicep  # Import the generate_frames function from bicep_curls.py
from arm_rowing import generate_frames_arm_rowing 
from squat_feedback import squat_feedback_bp
import datab  # Import the database connection file
import time
from chatbot import chatbot_bp  # Import the blueprint
from bson.objectid import ObjectId
from pymongo import MongoClient
import json
import pandas as pd





app = Flask(__name__)
app.secret_key = 'be454e0049196bc5c81986b1e8c19532c36ce5bc376bd4fb'  # Replace with a secure environment variable
app.register_blueprint(squat_feedback_bp)
app.register_blueprint(shoulder_feedback_bp)
app.register_blueprint(chatbot_bp)  # Register the blueprint

client = MongoClient('mongodb://localhost:27017/')
db = client['fitness_db']
collection = db['fitness_data']

data = pd.read_csv('dataset/indian_food.csv')

# Remove rows with missing calories
data = data.dropna(subset=['Calories'])


@app.route('/')
def home():
    if 'username' in session:
        username = session['username']
    else:
        username = None
    return render_template('main.html', username=username)

@app.route('/login1', methods=['GET', 'POST'])
def login1():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = datab.find_user_by_email(email)  # Fetch user by email from database
        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('home'))  # Redirect to dashboard or homepage after login
        else:
            flash('Incorrect credentials. Please try again.', 'danger')

    return render_template('login1.html')  # Render login page with any flashed messages

@app.route('/signup1', methods=['GET', 'POST'])
def signup1():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if email already exists
        if datab.find_user_by_email(email):
            flash('Email already exists. Please try a different email.', 'danger')
            return redirect(url_for('signup1'))

        # Hash the password before storing
        hashed_password = generate_password_hash(password)

        # Insert new user into the database
        datab.insert_user(username, email, hashed_password)
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login1'))

    return render_template('signup1.html')  # Render signup page with any flashed messages

@app.route('/contact_us')
def contact_us():
    return render_template('contact_us.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/exercise_selection_temp')
def exercise_selection_temp():
    return render_template('exercise_selection_temp.html')

@app.route('/detailed_info')
def detailed_info():
    return render_template('detailed_info.html')

@app.route('/squats')
def squats():
    return render_template('squats.html')

@app.route('/squat_tutorial')
def squat_tutorial():
    return render_template('squat_tutorial.html')


@app.route('/video_feed_squat')
def video_feed_squat():
    return Response(generate_frames_squat(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/reset_squat', methods=['POST'])
def reset_squat():
    global squat_count
    squat_count = 0
    return jsonify({'status': 'success', 'message': 'Squat count reset'})

@app.route('/bicep_curls')
def bicep_curls():
    return render_template('bicep_curl.html')

@app.route('/video_feed_bicep')
def video_feed_bicep():
    return Response(generate_frames_bicep(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/reset_curl', methods=['POST'])
def reset_curl():
    global curl_count
    curl_count = 0
    return jsonify({'status': 'success', 'message': 'Curl count reset'})

@app.route('/shoulder_raises')
def shoulder_raises():
    return render_template('shoulder_raises.html')

@app.route('/video_feed_shoulder')
def video_feed_shoulder():
    return Response(generate_frames_shoulder(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/reset_shoulder', methods=['POST'])
def reset_shoulder():
    global shoulder_raise_count
    shoulder_raise_count = 0
    return jsonify({'status': 'success', 'message': 'Shoulder raise count reset'})


@app.route('/lunges')
def lunges():
    return render_template('lunges.html')

@app.route('/video_feed_lunges')
def video_feed_lunges():
    return Response(generate_frames_lunges(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/reset_lunges', methods=['POST'])
def reset_lunges():
    global lunge_count
    lunge_count = 0
    return jsonify({'status': 'success', 'message': 'Lunge count reset'})

@app.route('/tricep_pushback')
def tricep_pushback():
    return render_template('tricep_pushback.html')

@app.route('/video_feed_tricep')
def video_feed_tricep():
    return Response(generate_frames_tricep(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/reset_tricep', methods=['POST'])
def reset_tricep_count():
    reset_tricep()
    return jsonify({'status': 'success', 'message': 'Tricep pushback count reset'})

@app.route('/lunges_info')
def lunges_info():
    return render_template('lunges_info.html')

@app.route('/bicep_curls_info')
def bicep_curls_info():
    return render_template('bicep_curls_info.html')

@app.route('/squats_info')
def squats_info():
    return render_template('squats_info.html')

@app.route('/tricep_pushback_info')
def tricep_pushback_info():
    return render_template('tricep_pushback_info.html')

@app.route('/hammer_curls_info')
def hammer_curls_info():
    return render_template('hammer_curls_info.html')

@app.route('/shoulder_raises_info')
def shoulder_raises_info():
    return render_template('shoulder_raises_info.html')

@app.route('/sumo_squats_info')
def sumo_squats_info():
    return render_template('sumo_squats_info.html')

@app.route('/lateral_raises_info')
def lateral_raises_info():
    return render_template('lateral_raises_info.html')

@app.route('/rear_delt_fly_info')
def rear_delt_fly_info():
    return render_template('rear_delt_fly_info.html')

@app.route('/deadlift_info')
def deadlift_info():
    return render_template('deadlift_info.html')

@app.route('/pullup_info')
def pullup_info():
    return render_template('pullup_info.html')

@app.route('/arm_rowing_info')
def arm_rowing_info():
    return render_template('arm_rowing_info.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')


@app.route("/arm_rowing")
def arm_rowing_page():
    return render_template("arm_rowing.html")

@app.route("/video_feed_arm_rowing")
def video_feed_arm_rowing():
    return Response(generate_frames_arm_rowing(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/reset_arm_rowing", methods=["POST"])
def reset_arm_rowing():
    global row_count, stage, start_time, elapsed_time
    row_count = 0
    stage = None
    start_time = None
    elapsed_time = 0
    return jsonify({"status": "success", "message": "Rowing count and timer reset."})

@app.route("/get_timer_arm_rowing")
def get_timer_arm_rowing():
    global start_time, elapsed_time
    if start_time:
        elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    return jsonify({"time": f"{minutes:02}:{seconds:02}"})

@app.route('/set_goal', methods=['GET', 'POST'])
def set_goal():
    if request.method == 'POST':
        session['goal'] = request.form['goal']
        return redirect(url_for('index'))
    return render_template('set_goal.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    selected_goal = request.form.get('goal') if request.method == 'POST' else session.get('goal')
    if selected_goal:
        session['goal'] = selected_goal  # Store goal in session for stats later
    records = list(collection.find())
    return render_template('index.html', goal=selected_goal, records=records)


@app.route('/add', methods=['POST'])
def add():
    data = {
        "date": request.form['date'],
        "exercise": request.form['exercise'],
        "duration": int(request.form['duration']),
        "weight": float(request.form['weight']),
        "steps": int(request.form['steps']) if request.form.get('steps') else None,
        "calories": int(request.form['calories']) if request.form.get('calories') else None,
        "heart_rate": int(request.form['heart_rate']) if request.form.get('heart_rate') else None,
        "reps": int(request.form['reps']) if request.form.get('reps') else None
    }
    collection.insert_one(data)
    return redirect(url_for('index'))

# Delete Record
@app.route('/delete/<record_id>')
def delete(record_id):
    collection.delete_one({"_id": ObjectId(record_id)})
    return redirect(url_for('index'))

# Update Record
@app.route('/update/<record_id>', methods=['GET', 'POST'])
def update(record_id):
    if request.method == 'POST':
        updated_data = {
            "date": request.form['date'],
            "exercise": request.form['exercise'],
            "duration": int(request.form['duration']),
            "weight": float(request.form['weight']),
            "steps": int(request.form['steps']) if request.form.get('steps') else None,
            "calories": int(request.form['calories']) if request.form.get('calories') else None,
            "heart_rate": int(request.form['heart_rate']) if request.form.get('heart_rate') else None,
            "reps": int(request.form['reps']) if request.form.get('reps') else None
        }
        collection.update_one({"_id": ObjectId(record_id)}, {"$set": updated_data})
        return redirect(url_for('index'))
    else:
        record = collection.find_one({"_id": ObjectId(record_id)})
        return render_template('update.html', record=record, record_id=record_id)

# Stats and Graphs
@app.route('/stats')
def stats():
    records = list(collection.find())
    dates = [rec['date'] for rec in records]
    weights = [rec['weight'] for rec in records]
    steps = [rec.get('steps', None) for rec in records]
    calories = [rec.get('calories', None) for rec in records]
    heart_rates = [rec.get('heart_rate', None) for rec in records]
    reps = [rec.get('reps', None) for rec in records]
    durations = [rec['duration'] for rec in records]

    goal = session['goal']
    comment = "📊 Add more data to see your progress."

    if len(weights) >= 2:
        diff = weights[-1] - weights[0]
        if goal == "gain":
            comment = "💪 Awesome! You're gaining weight effectively!" if diff > 2 else \
                      "👍 You're making progress. Keep going!" if diff > 0 else \
                      "⚠️ You might want to adjust your diet or training to gain better."
        elif goal == "lose":
            comment = "🔥 Great job! You're losing weight consistently!" if diff < -2 else \
                      "✅ You're on track. Stay focused!" if diff < 0 else \
                      "⚠️ Try to stay within your diet and workout plan."
        elif goal == "maintain":
            comment = "👌 Perfect! You're maintaining your weight well." if abs(diff) < 1 else \
                      "⚠️ There are some fluctuations. Keep an eye on your routine."

    return render_template('stats.html',
                           dates=json.dumps(dates),
                           weights=json.dumps(weights),
                           steps=json.dumps(steps),
                           calories=json.dumps(calories),
                           heart_rates=json.dumps(heart_rates),
                           reps=json.dumps(reps),
                           durations=json.dumps(durations),
                           comment=comment,
                           records=records)
    
@app.route("/diet_recommendation")
def diet_recommendation_page():
    return render_template("diet_recommendation.html")

@app.route('/recommend', methods=['POST'])
def recommend():
    age = int(request.form['age'])
    weight = float(request.form['weight'])
    height = float(request.form['height'])
    gender = request.form['gender']
    activity = request.form['activity']
    preference = request.form['preference']
    goal = request.form['goal']

    # Calculate BMR using Mifflin-St Jeor Equation
    if gender == 'Male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # Adjust BMR based on activity level
    activity_factors = {'Sedentary': 1.2, 'Moderate': 1.55, 'Active': 1.9}
    tdee = bmr * activity_factors[activity]

    # Adjust based on goal
    if goal == 'Weight Loss':
        daily_calories = tdee - 500
    elif goal == 'Weight Gain':
        daily_calories = tdee + 500
    else:
        daily_calories = tdee

    # Filter based on diet preference
    if preference == 'Veg':
        meals = data
    else:
        meals = data

    # Recommend meals randomly matching calorie ranges
    breakfast = meals.sample(1)
    lunch = meals.sample(1)
    dinner = meals.sample(1)

    total_calories = breakfast['Calories'].values[0] + lunch['Calories'].values[0] + dinner['Calories'].values[0]

    return render_template('result.html',
                           breakfast=breakfast.iloc[0],
                           lunch=lunch.iloc[0],
                           dinner=dinner.iloc[0],
                           daily_calories=int(daily_calories),
                           total_calories=int(total_calories))


if __name__ == '__main__':
    app.run(debug=True)
