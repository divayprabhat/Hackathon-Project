import os

class Config:
    # Camera settings
    camera_index = 0
    frame_width = 640
    frame_height = 480
    
    # File paths (relative to app directory)
    data_dir = "data"
    encodings_file = os.path.join(data_dir, 'face_encodings.pickle')
    excel_file = os.path.join(data_dir, 'attendance.xlsx')
    students_file = os.path.join(data_dir, 'students.xlsx')
    yearly_file = os.path.join(data_dir, 'attendance_yearly.xlsx')
    master_file = os.path.join(data_dir, 'attendance_master.xlsx')
    calendar_file = os.path.join(data_dir, 'attendance_calendar.xlsx')
    
    # Face recognition settings
    samples_per_student = 15  # Reduced for efficiency
    face_match_threshold = 0.45
    twin_match_threshold = 0.28
    process_every_n_frames = 5  # Process every 5th frame for better performance
    display_scale = 0.5  # Smaller scale for better performance
    
    # Model files
    shape_predictor_url = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
    face_rec_model_url = "http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2"
    shape_predictor_path = "shape_predictor_68_face_landmarks.dat"
    face_rec_model_path = "dlib_face_recognition_resnet_model_v1.dat"
    
    # Server settings
    server_host = "127.0.0.1"
    server_port = 5000
    
    def __init__(self):
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)

config = Config()
