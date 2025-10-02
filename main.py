import tkinter as tk
from tkinter import messagebox
import sys
import os
import atexit
from gui import FaceRecognitionApp
from cleanup import cleanup_temp_files

def check_dependencies():
    """Check if all required dependencies are available."""
    try:
        import cv2
        import dlib
        import numpy
        import pandas
        from PIL import Image
        return True
    except ImportError as e:
        return False, str(e)

def cleanup_on_exit():
    """Clean up temporary files on exit."""
    try:
        cleanup_temp_files()
    except Exception:
        pass  # Ignore cleanup errors on exit

def main():
    """Main application entry point."""
    # Check dependencies
    dep_check = check_dependencies()
    if not dep_check:
        error_msg = f"Missing dependencies: {dep_check[1]}\n\nPlease install requirements:\npip install -r requirements.txt"
        messagebox.showerror("Dependency Error", error_msg)
        return
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Register cleanup function
    atexit.register(cleanup_on_exit)
    
    try:
        root = tk.Tk()
        app = FaceRecognitionApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Application Error", f"Failed to start application: {e}")
    finally:
        # Clean up on exit
        cleanup_on_exit()

if __name__ == '__main__':
    main()
