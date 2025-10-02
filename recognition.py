import os
import pickle
import cv2
import numpy as np
import dlib
from datetime import datetime
from settings import config
from utils import download_and_extract
from attendance import AttendanceRegister
from crypto_utils import safe_temp_file

class FaceRecognitionSystem:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        # Download dlib models if missing
        download_and_extract(config.shape_predictor_url, config.shape_predictor_path)
        download_and_extract(config.face_rec_model_url, config.face_rec_model_path)
        self.shape_predictor = dlib.shape_predictor(config.shape_predictor_path)
        self.face_rec_model = dlib.face_recognition_model_v1(config.face_rec_model_path)

        self.known_face_encodings, self.known_face_names, self.known_face_ids = [], [], []
        self.known_face_unique_ids = []  # optional unique identifiers to disambiguate twins
        self.twins_pairs = set()  # set of frozenset({id1, id2}) pairs
        self._load_encodings()

        self.attendance_marked = set()
        self.today_date = datetime.now().date()
        self.register = AttendanceRegister()
        self.frame_count = 0
        self.last_results = []

    def _load_encodings(self):
        if os.path.exists(config.encodings_file): 
            from crypto_utils import load_key, decrypt_file 
            key = load_key("secret.key")
            tmp_path = safe_temp_file()
            try:
                # Step 1: decrypt into a temp file
                decrypt_file("face_encodings.pickle.enc", key, dst_path=tmp_path)
                # Step 2: load from decrypted temp
                with open(tmp_path, "rb") as f:
                    encodings = pickle.load(f)
                data = encodings
                self.known_face_encodings = data.get('encodings', [])
                self.known_face_names = data.get('names', [])
                self.known_face_ids = data.get('ids', [])
                self.known_face_unique_ids = data.get('unique_ids', [None] * len(self.known_face_ids))
                self.twins_pairs = set(map(frozenset, data.get('twins_pairs', [])))
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    def _save_encodings(self):
        data = {'encodings': self.known_face_encodings,
                'names': self.known_face_names,
                'ids': self.known_face_ids,
                'unique_ids': self.known_face_unique_ids,
                'twins_pairs': [list(p) for p in self.twins_pairs]}
        from crypto_utils import load_key, encrypt_file

        # Step 1: save temporarily
        tmp_path = safe_temp_file()
        try:
            with open(tmp_path, "wb") as f:
                pickle.dump(data, f)

            # Step 2: encrypt and save as .enc
            key = load_key("secret.key")
            encrypt_file(tmp_path, key, dst_path="face_encodings.pickle.enc")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


    def detect_and_encode(self, frame):
        """Detect faces and encode them for recognition."""
        small = cv2.resize(frame, (0, 0), fx=config.display_scale, fy=config.display_scale)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1,  # Reduced for better performance
            minNeighbors=5, 
            minSize=(50, 50)  # Smaller minimum size for better performance
        )
        results = []
        for (x, y, w, h) in faces:
            # Scale back to original frame coordinates
            l = int(x / config.display_scale)
            t = int(y / config.display_scale)
            r = int((x + w) / config.display_scale)
            b = int((y + h) / config.display_scale)
            
            # Extract face region
            face_rgb = cv2.cvtColor(frame[t:b, l:r], cv2.COLOR_BGR2RGB)
            if face_rgb.size == 0:
                continue
                
            try:
                dlib_rect = dlib.rectangle(0, 0, face_rgb.shape[1], face_rgb.shape[0])
                shape = self.shape_predictor(face_rgb, dlib_rect)
                encoding = np.array(self.face_rec_model.compute_face_descriptor(face_rgb, shape))
                results.append({'location': (l, t, r, b), 'encoding': encoding})
            except Exception:
                continue
        return results

    def compare_faces(self, encoding):
        if not self.known_face_encodings:
            return None, 'Unknown', 0.0
        encodings = np.array(self.known_face_encodings)
        distances = np.linalg.norm(encodings - encoding, axis=1)
        min_index = np.argmin(distances)
        min_distance = distances[min_index]
        if min_distance < config.face_match_threshold:
            return (self.known_face_ids[min_index], self.known_face_names[min_index], 1 - min_distance)
        return None, 'Unknown', 0.0

    def find_potential_twin_conflict(self, collected_encoding):
        if not self.known_face_encodings:
            return None, None
        encodings = np.array(self.known_face_encodings)
        distances = np.linalg.norm(encodings - collected_encoding, axis=1)
        min_index = int(np.argmin(distances))
        min_distance = float(distances[min_index])
        if min_distance < getattr(config, 'twin_match_threshold', 0.28):
            return {
                'index': min_index,
                'student_id': self.known_face_ids[min_index],
                'name': self.known_face_names[min_index],
                'unique_id': self.known_face_unique_ids[min_index] if self.known_face_unique_ids else None,
                'distance': min_distance
            }, min_distance
        return None, min_distance

    def replace_student_encodings(self, target_student_id, new_encodings, new_name=None, new_unique_id=None):
        # Remove all existing encodings for the student, then append new ones
        indices_to_keep = [i for i, sid in enumerate(self.known_face_ids) if sid != target_student_id]
        self.known_face_encodings = [self.known_face_encodings[i] for i in indices_to_keep]
        self.known_face_names = [self.known_face_names[i] for i in indices_to_keep]
        self.known_face_ids = [self.known_face_ids[i] for i in indices_to_keep]
        if self.known_face_unique_ids:
            self.known_face_unique_ids = [self.known_face_unique_ids[i] for i in indices_to_keep]
        for enc in new_encodings:
            self.known_face_encodings.append(enc)
            self.known_face_names.append(new_name)
            self.known_face_ids.append(target_student_id)
            if not self.known_face_unique_ids:
                self.known_face_unique_ids = [None] * (len(self.known_face_encodings) - 1)
            self.known_face_unique_ids.append(new_unique_id)
        self._save_encodings()

    def detect_and_recognize_faces(self, frame):
        self.frame_count += 1
        if self.frame_count % config.process_every_n_frames != 0:
            return self.last_results
        faces = self.detect_and_encode(frame)
        results = []
        for face in faces:
            sid, name, confidence = self.compare_faces(face['encoding'])
            results.append({'location': face['location'], 'name': name, 'id': sid, 'confidence': confidence})
        self.last_results = results
        return results

    def mark_attendance(self, sid, name):
        if sid is None or name == 'Unknown':
            return
        today = datetime.now().date()
        if today != self.today_date:
            self.attendance_marked.clear()
            self.today_date = today
        if sid not in self.attendance_marked:
            try:
                # Unified attendance method; marks 'P' by default
                self.register.mark_attendance(sid, name, "P")
                self.attendance_marked.add(sid)
                print(f"[SUCCESS] Marked attendance for {name} (ID: {sid})")
            except Exception as e:
                print(f"[ERROR] Error marking attendance for {name}: {e}")
