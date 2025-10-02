
"""
HTTPS-enabled Flask server for Smart Attendance System
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from attendance import AttendanceRegister
from recognition import FaceRecognitionSystem
import cv2
import numpy as np
from datetime import datetime
from settings import config
from crypto_utils import load_key, delete_key, generate_key
import ssl
import os
from pathlib import Path

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

def create_ssl_context():
    """Create SSL context for HTTPS."""
    cert_file = "ssl_certs/server.crt"
    key_file = "ssl_certs/server.key"
    
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("SSL certificates not found. Please run generate_ssl_cert.py first")
        return None
    
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)
        return context
    except Exception as e:
        print(f"Error loading SSL certificates: {e}")
        return None

# ---------------- RUN HTTPS SERVER ----------------
if __name__ == "__main__":
    print("Starting HTTPS Smart Attendance Server...")
    
    # Check for SSL certificates
    ssl_context = create_ssl_context()
    
    if ssl_context:
        print("SSL certificates loaded successfully")
        print("Server will run on HTTPS")
        print(f"Access at: https://{config.server_host}:{config.server_port}")
        print("Note: You may see a security warning for self-signed certificates")
        print(" Click 'Advanced' and 'Proceed to localhost' to continue")
        
        app.run(
            host=config.server_host,
            port=config.server_port,
            ssl_context=ssl_context,
            debug=True
        )
    else:
        print("Failed to load SSL certificates")
        print("Run: python generate_ssl_cert.py")
        print("Falling back to HTTP server...")

        # Fallback to HTTP
        app.run(
            host=config.server_host,
            port=config.server_port,
            debug=True
        )
