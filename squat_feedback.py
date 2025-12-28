from flask import Blueprint, render_template
import time

# Import the variables from your main squat tracking script
from squats import squat_count, start_time, timer_started

squat_feedback_bp = Blueprint('squat_feedback_bp', __name__)

def get_squat_feedback_data():
    # Calculate elapsed time only if timer was started
    if timer_started and start_time is not None:
        time_elapsed = int(time.time() - start_time)
    else:
        time_elapsed = 0
    return squat_count, time_elapsed

def compute_feedback(count, time_elapsed):
    if time_elapsed == 0 or count == 0:
        return None

    weight_kg = 70
    MET = 5.0

    duration_min = time_elapsed / 60
    count_per_min = count / duration_min
    avg_time_per_ex = time_elapsed / count
    calories_burnt = MET * weight_kg * (time_elapsed / 3600)
    efficiency = calories_burnt / count

    if count_per_min < 15:
        intensity = "Low"
    elif 15 <= count_per_min <= 30:
        intensity = "Medium"
    else:
        intensity = "High"

    return {
        "Calories Burnt": f"{round(calories_burnt, 2)} kcal",
        "Total Duration (sec)": time_elapsed,
        "Counts per Minute": round(count_per_min, 2),
        "Average Time per Exercise (sec)": round(avg_time_per_ex, 2),
        "Workout Intensity": intensity,
        "Efficiency Ratio": f"{round(efficiency, 4)} / 1"
    }

@squat_feedback_bp.route('/squat_feedback')
def show_feedback():
    count, time_elapsed = get_squat_feedback_data()
    feedback_data = compute_feedback(count, time_elapsed)
    return render_template("squat_feedback.html", feedback=feedback_data, count=count)
