from flask import Flask, render_template, Response, jsonify
import cv2
import mediapipe as mp
import numpy as np

app = Flask(__name__)

# Initialize MediaPipe Pose model
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Variables for squat counting
squat_count = 0
squat_in_progress = False
stand_up_threshold = 100
start_squat_threshold = 60

# Function to calculate the angle between three points
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle
    return angle

def generate_frames_squat():
    global squat_count, squat_in_progress
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

            landmarks = results.pose_landmarks.landmark
            left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP].y]
            left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE].y]
            left_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y]

            right_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y]
            right_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].y]
            right_ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].x, landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].y]

            left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
            right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)
            knee_angle = max(left_knee_angle, right_knee_angle)
            
            if knee_angle < start_squat_threshold:
                feedback = "Stand Up Straight!"
            elif start_squat_threshold <= knee_angle <= stand_up_threshold - 2:
                feedback = "Perfect Form!"
            elif knee_angle > stand_up_threshold:
                feedback = "Go Lower!"

            if knee_angle < start_squat_threshold and not squat_in_progress:
                squat_in_progress = True
            elif knee_angle > stand_up_threshold and squat_in_progress:
                squat_count += 1
                squat_in_progress = False

            cv2.putText(frame, f"Squats: {squat_count}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2) # pylint: disable=E1101
            cv2.putText(frame, feedback, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2) # pylint: disable=E1101

        _, buffer = cv2.imencode('.jpg', frame) # pylint: disable=E1101
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

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
    global squat_count, squat_in_progress
    squat_count = 0
    squat_in_progress = False
    return jsonify({'status': 'success', 'message': 'Squat count reset'})

if __name__ == "__main__":
    app.run(debug=True)
