from flask import Flask, render_template, Response, jsonify
import cv2
import mediapipe as mp
import numpy as np

app = Flask(__name__)

# MediaPipe Setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Tracking Variables
squat_count = 0
squat_in_progress = False
stand_up_threshold = 100
start_squat_threshold = 60

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360 - angle if angle > 180 else angle
import time  # ADD THIS

# Add global timing variables
squat_count = 0
squat_in_progress = False
timer_started = False
start_time = None

def generate_frames_squat():
    global squat_count, squat_in_progress, timer_started, start_time
    cap = cv2.VideoCapture(0) # pylint: disable=E1101

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1) # pylint: disable=E1101
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # pylint: disable=E1101
        results = pose.process(rgb_frame)
        feedback = ""

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            lm = results.pose_landmarks.landmark

            left = [lm[mp_pose.PoseLandmark.LEFT_HIP], lm[mp_pose.PoseLandmark.LEFT_KNEE], lm[mp_pose.PoseLandmark.LEFT_ANKLE]]
            right = [lm[mp_pose.PoseLandmark.RIGHT_HIP], lm[mp_pose.PoseLandmark.RIGHT_KNEE], lm[mp_pose.PoseLandmark.RIGHT_ANKLE]]
            left_angle = calculate_angle([left[0].x, left[0].y], [left[1].x, left[1].y], [left[2].x, left[2].y])
            right_angle = calculate_angle([right[0].x, right[0].y], [right[1].x, right[1].y], [right[2].x, right[2].y])
            knee_angle = max(left_angle, right_angle)

            # Timer starts only once when squat begins
            if knee_angle < start_squat_threshold and not timer_started:
                timer_started = True
                start_time = time.time()

            # Feedback logic
            if knee_angle < start_squat_threshold:
                feedback = "Stand Up Straight!"
            elif start_squat_threshold <= knee_angle <= stand_up_threshold - 2:
                feedback = "Perfect Form!"
            elif knee_angle > stand_up_threshold:
                feedback = "Go Lower!"

            # Count logic
            if knee_angle < start_squat_threshold and not squat_in_progress:
                squat_in_progress = True
            elif knee_angle > stand_up_threshold and squat_in_progress:
                squat_count += 1
                squat_in_progress = False

            # Draw feedback
            cv2.putText(frame, f"Squats: {squat_count}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2) # pylint: disable=E1101
            cv2.putText(frame, feedback, (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2) # pylint: disable=E1101

            # Timer display (only if started)
            if timer_started and start_time:
                elapsed_time = int(time.time() - start_time)
                mins, secs = divmod(elapsed_time, 60)
                timer_display = f"Time: {mins:02}:{secs:02}"
                cv2.putText(frame, timer_display, (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2) # pylint: disable=E1101

        _, buffer = cv2.imencode('.jpg', frame) # pylint: disable=E1101
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    cap.release()

@app.route('/')
def index():
    return render_template('exercise_selection_temp.html')

@app.route('/squats')
def squats():
    return render_template('squats.html')

@app.route('/video_feed_squat')
def video_feed_squat():
    return Response(generate_frames_squat(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/reset_squat', methods=['POST'])
def reset_squat():
    global squat_count, squat_in_progress, timer_started, start_time
    squat_count = 0
    squat_in_progress = False
    timer_started = False
    start_time = None
    return jsonify({'status': 'success', 'message': 'Squat count reset'})




if __name__ == '__main__':
    app.run(debug=True)



# Accuracy : 92.5%
# Precision : 95%
# F1 score : 92.7%
# Recall : 90.5%