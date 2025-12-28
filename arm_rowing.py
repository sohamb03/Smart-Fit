from flask import Flask, render_template, Response, jsonify
import cv2
import mediapipe as mp
import time

app = Flask(__name__)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

row_count = 0
stage = None
start_time = None
elapsed_time = 0

def get_coords(landmarks, part):
    try:
        point = landmarks[mp_pose.PoseLandmark[part].value]
        return point.x, point.y
    except:
        return 0, 0

def generate_frames_arm_rowing():
    global row_count, stage, start_time, elapsed_time

    cap = cv2.VideoCapture(0)  # pylint: disable=E1101

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)  # pylint: disable=E1101
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # pylint: disable=E1101
        results = pose.process(rgb)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            landmarks = results.pose_landmarks.landmark

            try:
                shoulder_x, _ = get_coords(landmarks, "RIGHT_SHOULDER")
                elbow_x, _ = get_coords(landmarks, "RIGHT_ELBOW")
                wrist_x, _ = get_coords(landmarks, "RIGHT_WRIST")

                # Stage detection based on horizontal motion (x-coordinates)
                if wrist_x < elbow_x and elbow_x < shoulder_x:
                    stage = "extend"
                if wrist_x > elbow_x and stage == "extend":
                    stage = "row"
                    row_count += 1
                    if not start_time:
                        start_time = time.time()

                # Display data on screen
                cv2.putText(frame, f"Rows: {row_count}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)  # pylint: disable=E1101
                cv2.putText(frame, f"Stage: {stage}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)  # pylint: disable=E1101

                if start_time:
                    elapsed_time = time.time() - start_time
                    mins = int(elapsed_time // 60)
                    secs = int(elapsed_time % 60)
                    cv2.putText(frame, f"Time: {mins:02}:{secs:02}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)  # pylint: disable=E1101

            except Exception as e:
                print("Error in landmark processing:", e)

        ret, buffer = cv2.imencode('.jpg', frame)  # pylint: disable=E1101
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

@app.route("/arm_rowing")
def arm_rowing_page():
    return render_template("arm_rowing.html")

@app.route("/video_feed_arm_rowing")
def video_feed_arm_rowing():
    return Response(generate_frames_arm_rowing(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/reset_arm_rowing", methods=["POST"])
def reset_arm_rowing():
    global row_count, stage, start_time, elapsed_time
    row_count = 0
    stage = None
    start_time = None
    elapsed_time = 0
    return jsonify({"status": "success", "message": "Rowing count and timer reset."})

@app.route("/get_timer_arm_rowing")
def get_timer_arm_rowing():
    global start_time, elapsed_time
    if start_time:
        elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    return jsonify({"time": f"{minutes:02}:{seconds:02}"})

if __name__ == "__main__":
    app.run(debug=True)



