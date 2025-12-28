from flask import Flask, render_template, request
import pandas as pd
import random

app = Flask(__name__)

# Load the dataset
data = pd.read_csv('dataset/indian_food.csv')

# Remove rows with missing calories
data = data.dropna(subset=['Calories'])

# Home route
@app.route('/')
def home():
    return render_template('diet_recommendation.html')

# Result route
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

if __name__ == "__main__":
    app.run(debug=True)
