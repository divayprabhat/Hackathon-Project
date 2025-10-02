from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from attendance import AttendanceRegister
from recognition import FaceRecognitionSystem
import cv2
import numpy as np
from datetime import datetime
from settings import config
from crypto_utils import load_key, delete_key, generate_key

app = Flask(__name__)
CORS(app)

# Initialize systems
attendance = AttendanceRegister()
face_system = FaceRecognitionSystem()
SECRET_KEY = load_key()

# ---------------- ROUTES ----------------
@app.route("/", methods=["GET"])
def home():
    """Home route to serve the website."""
    try:
        with open("website.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error loading website: {e}", 500

@app.route("/website.html", methods=["GET"])
def serve_website():
    """Serve the website HTML file."""
    return send_from_directory(".", "website.html")

@app.route("/init_attendance", methods=["GET"])
def init_attendance():
    try:
        attendance._ensure_register()
        attendance._ensure_calendar()
        attendance._ensure_yearly()
        attendance._ensure_master()
        return jsonify({"success": True, "message": "Attendance system initialized"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/get_attendance", methods=["GET"])
def get_attendance():
    try:
        import pandas as pd
        df_master = attendance._normalize_schemas()
        df_master = pd.read_excel(attendance.master_file)
        records = []
        for _, row in df_master.iterrows():
            records.append({
                "StudentID": row["StudentID"],
                "Name": row["Name"],
                "Date": row["Date"],
                "Status": row["Status"]
            })
        return jsonify(records), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/update_attendance", methods=["POST"])
def update_attendance():
    try:
        data = request.get_json()
        today_str = datetime.now().date().isoformat()
        for record in data:
            student_id = int(record["StudentID"])
            name = record.get("Name", "Unknown")
            status = record.get("Status", "P").strip().upper()
            status = "P" if status == "P" else "A"
            attendance.mark_attendance(student_id, name, status)
        return jsonify({"success": True, "message": "Attendance updated"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/add_student", methods=["POST"])
def add_student():
    try:
        data = request.get_json()
        student_id = int(data["StudentID"])
        name = data["Name"]
        attendance.add_student(student_id, name)
        return jsonify({"success": True, "message": f"Student {name} added"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/reset_attendance", methods=["POST"])
def reset_attendance():
    try:
        attendance.reset_all()
        return jsonify({"success": True, "message": "All attendance data reset"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/mark_face_attendance", methods=["POST"])
def mark_face_attendance():
    try:
        import base64
        from io import BytesIO
        from PIL import Image

        data = request.get_json()
        img_b64 = data.get("image")
        if not img_b64:
            return jsonify({"success": False, "error": "No image provided"}), 400

        img_bytes = base64.b64decode(img_b64)
        img = Image.open(BytesIO(img_bytes))
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        results = face_system.detect_and_recognize_faces(frame)
        for res in results:
            sid, name = res['id'], res['name']
            face_system.mark_attendance(sid, name)

        return jsonify({"success": True, "results": results}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------- KEY MANAGEMENT ----------------
@app.route("/reset_key", methods=["POST"])
def reset_key():
    try:
        deleted = delete_key()
        new_key = generate_key()
        return jsonify({"success": True, "message": "Key reset successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)