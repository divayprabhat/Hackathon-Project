import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import cv2
from PIL import Image, ImageTk
import os
import pandas as pd
from datetime import datetime
from settings import config
from recognition import FaceRecognitionSystem

class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Attendance System")
        self.root.geometry("1000x700")
        
        # Initialize systems
        try:
            self.face_system = FaceRecognitionSystem()
            self.cap = cv2.VideoCapture(config.camera_index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize camera or face recognition: {e}")
            self.face_system = None
            self.cap = None
        
        self.setup_ui()
        self.load_attendance_data()
        self.auto_refresh_attendance()
        self.running = True
        self.update_frame()
    
    def setup_ui(self):
        """Setup the user interface."""
        # Main container
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Camera and controls
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill="both", expand=True)
        
        # Camera display
        self.video_label = tk.Label(left_frame, text="Camera Loading...", bg="black", fg="white")
        self.video_label.pack(pady=5)
        
        # Control buttons
        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(pady=10)
        
        # Simple button layout
        tk.Button(btn_frame, text="Import Students", command=self.import_students_from_excel, 
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Add Student", command=self.add_student_to_excel,
                 bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.update_attendance,
                 bg="#FF9800", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Reset", command=self.reset_system,
                 bg="#F44336", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        # Status log
        log_frame = tk.Frame(left_frame)
        log_frame.pack(fill="x", pady=5)
        tk.Label(log_frame, text="System Status:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.log_text = tk.Text(log_frame, height=6, state="disabled", bg="#f0f0f0")
        self.log_text.pack(fill="x")
        
        # Right side - Attendance table
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill="both", expand=True, padx=(10, 0))
        
        # Table controls
        controls_frame = tk.Frame(right_frame)
        controls_frame.pack(fill="x", pady=(0, 5))
        tk.Label(controls_frame, text="Today's Attendance", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        tk.Button(controls_frame, text="Full View", command=self.toggle_view,
                 bg="#9C27B0", fg="white").pack(side=tk.RIGHT)
        
        # Attendance table
        tree_frame = tk.Frame(right_frame)
        tree_frame.pack(fill="both", expand=True)
        
        self.tree = ttk.Treeview(tree_frame, show="headings")
        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        yscroll.pack(side=tk.RIGHT, fill="y")
        
        self.compact_view = True

    # ---------------- Logging ----------------
    def log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {msg}\n")
        self.log_text.config(state="disabled")
        self.log_text.see(tk.END)

    # ---------------- Video Frame Update ----------------
    def update_frame(self):
        try:
            if self.cap is None or self.face_system is None:
                self.video_label.configure(text="Camera or Face Recognition not available", bg="red", fg="white")
                if self.running:
                    self.root.after(1000, self.update_frame)
                return
                
            ret, frame = self.cap.read()
            if not ret:
                return
            frame = cv2.flip(frame, 1)
            results = self.face_system.detect_and_recognize_faces(frame)
            for res in results:
                (l, t, r, b) = res["location"]
                name, sid = res["name"], res["id"]
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (l, t), (r, b), color, 2)
                cv2.putText(frame, f"{name}", (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                self.face_system.mark_attendance(sid, name)
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        except Exception as e:
            self.log(f"[ERROR] Frame update error: {e}")
        finally:
            if self.running:
                self.root.after(10, self.update_frame)

    # ---------------- Student Import ----------------
    def import_students_from_excel(self):
        if not os.path.exists(config.students_file):
            df = pd.DataFrame(columns=["StudentID", "Name"])
            df.to_excel(config.students_file, index=False)
            messagebox.showinfo("Info", f"No Excel found. A new file was created at:\n{config.students_file}")
            return
        try:
            df = pd.read_excel(config.students_file)
            if "StudentID" not in df.columns or "Name" not in df.columns:
                messagebox.showerror("Error", "Excel must contain 'StudentID' and 'Name' columns")
                return
            # Filter out rows with missing/blank values
            df = df.dropna(subset=["StudentID", "Name"]).copy()
            df["Name"] = df["Name"].astype(str).str.strip()
            df = df[df["Name"] != ""]
            for _, row in df.iterrows():
                sid, name = row["StudentID"], row["Name"]
                self.face_system.register.add_student(sid, name)
            self.load_attendance_data()
            self.log("Students imported from Excel successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import students: {e}")

    # ---------------- Add Student ----------------
    def add_student_to_excel(self):
        """Add a new student to the system."""
        # Get student information
        sid = simpledialog.askinteger("Add Student", "Enter Student ID:")
        if not sid:
            return
            
        name = simpledialog.askstring("Add Student", "Enter Student Name:")
        if not name:
            return

        # Check if student already exists
        if not os.path.exists(config.excel_file):
            df = pd.DataFrame(columns=["StudentID", "Name"])
            df.to_excel(config.excel_file, index=False)

        try:
            df = pd.read_excel(config.excel_file)
            if sid in df["StudentID"].values:
                messagebox.showwarning("Warning", f"Student ID {sid} already exists!")
                return

            # Add to Excel
            new_row = pd.DataFrame([[sid, name]], columns=["StudentID", "Name"])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_excel(config.excel_file, index=False)

            # Capture face samples
            messagebox.showinfo("Face Capture", f"Look at the camera. Capturing {config.samples_per_student} samples for {name}")
            collected = self.capture_samples()

            if collected:
                # Simple conflict check
                conflict, _ = self.face_system.find_potential_twin_conflict(collected[0])
                if conflict and conflict.get('student_id') != sid:
                    other_name = conflict.get('name')
                    is_twins = messagebox.askyesno(
                        "Similar Face Detected",
                        f"This face looks very similar to {other_name}.\nAre they the same person or twins?"
                    )
                    if not is_twins:
                        messagebox.showinfo("Info", "Please ensure the person is looking directly at the camera.")
                        collected = self.capture_samples(prompt="Please look directly at camera for better recognition")

                # Add encodings
                for enc in collected:
                    self.face_system.known_face_encodings.append(enc)
                    self.face_system.known_face_names.append(name)
                    self.face_system.known_face_ids.append(sid)
                    if not self.face_system.known_face_unique_ids:
                        self.face_system.known_face_unique_ids = [None] * (len(self.face_system.known_face_encodings) - 1)
                    self.face_system.known_face_unique_ids.append(None)
                
                self.face_system._save_encodings()
                self.face_system.register.add_student(sid, name)
                self.load_attendance_data()
                self.log(f"[SUCCESS] Added {name} (ID: {sid}) successfully!")
            else:
                messagebox.showwarning("Warning", "Failed to capture face samples. Please try again.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add student: {e}")

    def capture_samples(self, prompt=None):
        if prompt:
            messagebox.showinfo("Capture", prompt)
        collected = []
        attempts = 0
        while len(collected) < config.samples_per_student and attempts < config.samples_per_student * 5:
            attempts += 1
            ret, frame = self.cap.read()
            frame = cv2.flip(frame, 1)
            detections = self.face_system.detect_and_encode(frame)
            if len(detections) == 1:
                collected.append(detections[0]["encoding"])
            self.root.update_idletasks()
            self.root.update()
        return collected

    # ---------------- Update Attendance ----------------
    def update_attendance(self):
        self.load_attendance_data()
        self.log("Attendance updated & reloaded.")

    # ---------------- Show File Paths ----------------
    def show_paths(self):
        paths = f"Attendance Excel: {os.path.abspath(config.excel_file)}\n" \
                f"Yearly Excel: {os.path.abspath(config.yearly_file)}\n" \
                f"Master Excel: {os.path.abspath(getattr(config,'master_file','attendance_master.xlsx'))}\n" \
                f"Encodings: {os.path.abspath(config.encodings_file)}"
        messagebox.showinfo("File Paths", paths)

    # ---------------- Load Attendance to Tree ----------------
    def load_attendance_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not os.path.exists(config.excel_file):
            return
        df = pd.read_excel(config.excel_file)
        # Hide rows with NaN/blank StudentID or Name
        if "StudentID" in df.columns and "Name" in df.columns:
            df = df.dropna(subset=["StudentID", "Name"]).copy()
            df["Name"] = df["Name"].astype(str).str.strip()
            df = df[df["Name"] != ""]
        # Ensure clean, compact default view
        if self.compact_view:
            today_col = datetime.now().date().isoformat()
            display_df = df.copy()
            if today_col not in display_df.columns:
                display_df[today_col] = 'A'
            display_df = display_df[["StudentID", "Name", today_col]]
            columns = list(display_df.columns)
            self.tree["columns"] = columns
            for col in columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=140 if col == "Name" else 110)
            for _, row in display_df.iterrows():
                self.tree.insert("", "end", values=[row[c] for c in columns])
        else:
            columns = list(df.columns)
            self.tree["columns"] = columns
            for col in columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=100)
            for _, row in df.iterrows():
                self.tree.insert("", "end", values=list(row))

    def toggle_view(self):
        self.compact_view = not self.compact_view
        self.load_attendance_data()

    # ---------------- Auto Refresh ----------------
    def auto_refresh_attendance(self):
        self.load_attendance_data()
        self.root.after(10000, self.auto_refresh_attendance)

    # ---------------- Reset System ----------------
    def reset_system(self):
        confirm = messagebox.askyesno("Confirm Reset", "This will erase ALL faces and attendance records. Continue?")
        if not confirm:
            return

        # Delete face encodings
        if os.path.exists(config.encodings_file):
            os.remove(config.encodings_file)
        self.face_system.known_face_encodings.clear()
        self.face_system.known_face_names.clear()
        self.face_system.known_face_ids.clear()
        self.face_system.attendance_marked.clear()

        # Reset all registers
        self.face_system.register.reset_all()

        # Reload GUI treeview
        self.load_attendance_data()
        self.log("System reset: all faces and attendance cleared, registers recreated.")

    # ---------------- Quit ----------------
    def quit_app(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()
        self.root.destroy()


# ---------------- MAIN ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()