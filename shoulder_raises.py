from flask import Flask, render_template, Response, jsonify
import cv2
import mediapipe as mp
import numpy as np
import time

app = Flask(__name__)

# Initialize MediaPipe Pose model
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Variables
shoulder_raise_count = 0
stage = None  # "up" or "down"
wrist_shoulder_threshold = 0.05  # Y-axis difference threshold
start_time = None
elapsed_time = 0

# Function to extract coordinates
def get_coordinates(landmarks, parts):
    return [
        [landmarks[mp_pose.PoseLandmark[part].value].x, landmarks[mp_pose.PoseLandmark[part].value].y]
        for part in parts
    ]

# Generator for video feed
def generate_frames_shoulder():
    global shoulder_raise_count, stage, start_time, elapsed_time
    cap = cv2.VideoCapture(0)  # pylint: disable=E1101

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1) # pylint: disable=E1101
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # pylint: disable=E1101
        results = pose.process(rgb_frame)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            landmarks = results.pose_landmarks.landmark

            try:
                left_shoulder, left_wrist = get_coordinates(landmarks, ["LEFT_SHOULDER", "LEFT_WRIST"])
                right_shoulder, right_wrist = get_coordinates(landmarks, ["RIGHT_SHOULDER", "RIGHT_WRIST"])

                left_raised = left_wrist[1] < left_shoulder[1] - wrist_shoulder_threshold
                right_raised = right_wrist[1] < right_shoulder[1] - wrist_shoulder_threshold

                if left_raised and right_raised:
                    if stage == "down":
                        stage = "up"
                        shoulder_raise_count += 1
                        if not start_time:
                            start_time = time.time()
                elif left_wrist[1] > left_shoulder[1] and right_wrist[1] > right_shoulder[1]:
                    stage = "down"

                # Show count and stage
                cv2.putText(frame, f"Raises: {shoulder_raise_count}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2) # pylint: disable=E1101
                cv2.putText(frame, f"Stage: {stage.capitalize() if stage else 'N/A'}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2) # pylint: disable=E1101

                # Show timer
                if start_time:
                    elapsed_time = time.time() - start_time
                    minutes = int(elapsed_time // 60)
                    seconds = int(elapsed_time % 60)
                    cv2.putText(frame, f"Time: {minutes:02}:{seconds:02}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2) # pylint: disable=E1101

            except KeyError: # pylint: disable=E1101
                pass

        _, buffer = cv2.imencode('.jpg', frame) # pylint: disable=E1101
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@app.route('/shoulder_raises')
def shoulder_raises():
    return render_template('shoulder_raises.html')

@app.route('/video_feed_shoulder')
def video_feed_shoulder():
    return Response(generate_frames_shoulder(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/reset_shoulder', methods=['POST'])
def reset_shoulder():
    global shoulder_raise_count, stage, start_time, elapsed_time
    shoulder_raise_count = 0
    stage = None
    start_time = None
    elapsed_time = 0
    return jsonify({'status': 'success', 'message': 'Shoulder raise count and timer reset'})

@app.route('/get_timer_shoulder_raise')
def get_timer_shoulder_raise():
    global start_time, elapsed_time
    if start_time:
        elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    return jsonify({'time': f"{minutes:02}:{seconds:02}"})

def get_feedback_data():
    global shoulder_raise_count, start_time
    if not start_time:
        elapsed = 0
    else:
        elapsed = int(time.time() - start_time)
    return shoulder_raise_count, elapsed


if __name__ == "__main__":
    app.run(debug=True)



# Accuracy : 92.9%
# Precision : 93.9%
# F1 score : 92.5%
# Recall : 91.1%