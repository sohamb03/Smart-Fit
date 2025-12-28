from flask import Response
import cv2
import mediapipe as mp
import numpy as np

# MediaPipe setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Counter variables
tricep_count = 0
stage = None  # 'push' or 'back'

# Utility functions
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

def get_coords(landmarks, name):
    lm = mp_pose.PoseLandmark[name].value
    return [landmarks[lm].x, landmarks[lm].y]

def generate_frames_tricep():
    global tricep_count, stage
    cap = cv2.VideoCapture(0)  # pylint: disable=E1101

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)  # pylint: disable=E1101
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # pylint: disable=E1101
        results = pose.process(rgb)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            landmarks = results.pose_landmarks.landmark

            try:
                # Get keypoints
                left_shoulder = get_coords(landmarks, 'LEFT_SHOULDER')
                left_elbow = get_coords(landmarks, 'LEFT_ELBOW')
                left_wrist = get_coords(landmarks, 'LEFT_WRIST')
                left_hip = get_coords(landmarks, 'LEFT_HIP')

                # Check if torso is bent forward
                torso_angle = calculate_angle(left_shoulder, left_hip, [left_hip[0], left_hip[1] - 0.1])
                is_bent = torso_angle > 15  # Adjust threshold as needed

                # Elbow extension angle
                angle = calculate_angle(left_shoulder, left_elbow, left_wrist)

                # Pushback counting logic
                if angle > 150 and is_bent:
                    stage = "push"
                if angle < 70 and stage == "push" and is_bent:
                    tricep_count += 1
                    stage = "back"

                # Display info
                cv2.putText(frame, f'Tricep Pushbacks: {tricep_count}', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)  # pylint: disable=E1101
                cv2.putText(frame, f'Stage: {stage if stage else "N/A"}', (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)  # pylint: disable=E1101

                if not is_bent:
                    cv2.putText(frame, 'Bend your torso forward!', (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)  # pylint: disable=E1101

            except Exception as e:
                print("Error processing frame:", e)
                continue
        else:
            continue  # skip to next frame if no landmarks

        # Encode and yield frame
        _, buffer = cv2.imencode('.jpg', frame)  # pylint: disable=E1101
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

def reset_tricep():
    global tricep_count
    tricep_count = 0



