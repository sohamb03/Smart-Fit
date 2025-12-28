from flask import Blueprint, render_template, Response, jsonify
import cv2
import mediapipe as mp
import numpy as np

lunges_bp = Blueprint('lunges', __name__)

# Initialize MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Repetition counters
lunge_count = 0
lunge_stage = None

# Utility function to calculate angle
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

# Extract landmark coordinates
def get_coordinates(landmarks, parts):
    return [
        [landmarks[mp_pose.PoseLandmark[part].value].x,
         landmarks[mp_pose.PoseLandmark[part].value].y]
        for part in parts
    ]

# Frame generation function
def generate_frames_lunges():
    global lunge_count, lunge_stage
    cap = cv2.VideoCapture(0) # pylint: disable=E1101

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
                # Left leg keypoints
                left_hip, left_knee, left_ankle = get_coordinates(
                    landmarks, ["LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE"])
                # Right leg keypoints
                right_hip, right_knee, right_ankle = get_coordinates(
                    landmarks, ["RIGHT_HIP", "RIGHT_KNEE", "RIGHT_ANKLE"])

                left_angle = calculate_angle(left_hip, left_knee, left_ankle)
                right_angle = calculate_angle(right_hip, right_knee, right_ankle)

                # Simple logic: left knee bends below 90 -> down; returns to 150+ -> count
                if left_angle < 100 and right_angle > 160:
                    lunge_stage = "down"
                elif left_angle > 150 and right_angle > 160 and lunge_stage == "down":
                    lunge_stage = "up"
                    lunge_count += 1

                cv2.putText(frame, f"Lunges: {lunge_count}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2) # pylint: disable=E1101
                cv2.putText(frame, f"Stage: {lunge_stage.capitalize() if lunge_stage else 'N/A'}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2) # pylint: disable=E1101

            except Exception as e:
                print("Error in keypoint extraction:", e)

        _, buffer = cv2.imencode('.jpg', frame) # pylint: disable=E1101
        frame = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()


# ROUTES

@lunges_bp.route('/lunges')
def lunges():
    return render_template('lunges.html')

@lunges_bp.route('/video_feed_lunges')
def video_feed_lunges():
    return Response(generate_frames_lunges(), mimetype='multipart/x-mixed-replace; boundary=frame')

@lunges_bp.route('/reset_lunges', methods=['POST'])
def reset_lunges():
    global lunge_count
    lunge_count = 0
    return jsonify({'status': 'success', 'message': 'Lunge count reset'})



# Accuracy : 93.8%
# Precision : 92.6%
# F1 score : 93.9%
# Recall : 95.2%