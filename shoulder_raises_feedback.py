from flask import Blueprint, render_template
from shoulder_raises import get_feedback_data  # Import the new function

shoulder_feedback_bp = Blueprint('shoulder_feedback_bp', __name__)

def compute_feedback(count, time_elapsed):
    if time_elapsed == 0 or count == 0:
        return None

    weight_kg = 70
    MET = 5.0

    duration_sec = int(time_elapsed)
    duration_min = duration_sec / 60
    count_per_min = count / duration_min
    avg_time_per_ex = duration_sec / count
    calories_burnt = MET * weight_kg * (duration_sec / 3600)
    efficiency = calories_burnt / count

    if count_per_min < 15:
        intensity = "Low"
    elif 15 <= count_per_min <= 30:
        intensity = "Medium"
    else:
        intensity = "High"

    return {
        "Calories Burnt": f"{round(calories_burnt, 2)} kcal",
        "Total Duration (sec)": duration_sec,
        "Counts per Minute": round(count_per_min, 2),
        "Average Time per Exercise (sec)": round(avg_time_per_ex, 2),
        "Workout Intensity": intensity,
        "Efficiency Ratio": f"{round(efficiency, 4)} / 1 "
    }

@shoulder_feedback_bp.route('/shoulder_raises_feedback')
def show_feedback():
    count, time_elapsed = get_feedback_data()
    feedback_data = compute_feedback(count, time_elapsed)
    return render_template("shoulder_raises_feedback.html", feedback=feedback_data)
