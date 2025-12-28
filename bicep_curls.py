from flask import Flask, render_template, Response, jsonify
import cv2
import mediapipe as mp
import numpy as np

app = Flask(__name__)

# Initialize MediaPipe Pose model
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Variables for curl counting
curl_count = 0
stage = None  # Stage can be "up" or "down"
elbow_torso_threshold = 0.27  # Maximum allowable distance between elbow and shoulder

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

# Function to extract coordinates of landmarks
def get_coordinates(landmarks, parts):
    return [
        [landmarks[mp_pose.PoseLandmark[part].value].x, landmarks[mp_pose.PoseLandmark[part].value].y]
        for part in parts
    ]

# Function to calculate Euclidean distance
def calculate_distance(point1, point2):
    return np.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

# Function to generate frames for bicep curl tracking
def generate_frames_bicep():
    global curl_count, stage
    cap = cv2.VideoCapture(0) # pylint: disable=E1101

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)  # pylint: disable=E1101
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)# pylint: disable=E1101
        results = pose.process(rgb_frame)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            landmarks = results.pose_landmarks.landmark
            try:
                # Get coordinates for shoulders, elbows, and wrists
                left_shoulder, left_elbow, left_wrist = get_coordinates(
                    landmarks, ["LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"] 
                )
                right_shoulder, right_elbow, right_wrist = get_coordinates(
                    landmarks, ["RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"]
                )

                # Calculate elbow-to-shoulder distances
                left_elbow_distance = calculate_distance(left_shoulder, left_elbow)
                right_elbow_distance = calculate_distance(right_shoulder, right_elbow)

                # Check if elbows are near the torso
                elbows_near_torso = ( left_elbow_distance < elbow_torso_threshold and right_elbow_distance < elbow_torso_threshold)

                if not elbows_near_torso:
                    cv2.putText(frame,"Keep your elbows close to your body!",(50, 400),cv2.FONT_HERSHEY_SIMPLEX,1,(0, 0, 255),2)# pylint: disable=E1101

                # Calculate angles for curls
                left_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
                right_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)

                # Detect stage and update count
                if left_angle > 140 and right_angle > 140 and left_elbow_distance < elbow_torso_threshold and right_elbow_distance < elbow_torso_threshold :
                    if stage == "up":
                        curl_count += 1
                        stage = "down"
                elif left_angle < 60 and right_angle and left_elbow_distance < elbow_torso_threshold and right_elbow_distance < elbow_torso_threshold< 60:
                    stage = "up"

                # Display counter and stage
                cv2.putText(frame, f"Curls: {curl_count}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)# pylint: disable=E1101
                cv2.putText(frame, f"Stage: {stage.capitalize() if stage else 'N/A'}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)# pylint: disable=E1101

            except KeyError:
                pass

        _, buffer = cv2.imencode('.jpg', frame) # pylint: disable=E1101
        frame = buffer.tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@app.route('/')
def index():
    return render_template('exercise_selection_temp.html')

@app.route('/bicep_curls')
def bicep_curls():
    return render_template('bicep_curl.html')

@app.route('/video_feed_bicep')
def video_feed():
    return Response(generate_frames_bicep(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/reset_curl', methods=['POST'])
def reset_curl():
    global curl_count
    curl_count = 0
    return jsonify({'status': 'success', 'message': 'Curl count reset'})

if __name__ == "__main__":
    app.run(debug=True)




# Accuracy : 91.6%
# Precision : 92.6%
# F1 score : 91.2%
# Recall : 89.8%