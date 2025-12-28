from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key for production

# MongoDB Setup
client = MongoClient('mongodb://localhost:27017/')
db = client['fitness_db']
collection = db['fitness_data']

# Global check for goal selection before any request
@app.before_request
def require_goal():
    allowed_routes = ['set_goal', 'static']
    if request.endpoint not in allowed_routes and 'goal' not in session:
        return redirect(url_for('set_goal'))

# Home route
@app.route('/')
def index():
    records = collection.find()
    return render_template('index.html', records=records)

# Set Goal Route
@app.route('/set-goal', methods=['GET', 'POST'])
def set_goal():
    if request.method == 'POST':
        session['goal'] = request.form['goal']
        return redirect(url_for('index'))
    return render_template('set_goal.html')

# Add Fitness Record
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
            comment = "💪 Awesome! You're gaining weight effectively! Keep going you will reach your goal soon" if diff > 2 else \
                      "👍 You're making progress. Keep going and try to concentrate more on your diet for better results !" if diff > 0 else \
                      "⚠️ You might want to adjust your diet or training to gain better."
        elif goal == "lose":
            comment = "🔥 Great job! You're losing weight consistently according to your Progress tracking!,keep Going you will Achieve your goal shortly" if diff < -2 else \
                      "✅ You're on track. Stay focused and try to work a little more harder !" if diff < 0 else \
                      "⚠️ Try to stay within your diet and workout plan.If you are within your plan, Please revise your exercise and diet plan "
        elif goal == "maintain":
            comment = "👌 Perfect! You're maintaining your weight well." if abs(diff) < 1 else \
                      "⚠️ There are some fluctuations. Keep an eye on your routine, else make modifications in your diet and exercise routine."

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

if __name__ == '__main__':
    app.run(debug=True)
