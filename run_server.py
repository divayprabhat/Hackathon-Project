
"""
Face Recognition Attendance System - Server Launcher
This script launches the Flask server from the organized project structure.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the server
from server import app

if __name__ == "__main__":
    print("Starting Face Recognition Attendance System...")
    print("Server will be available at: http://127.0.0.1:5000")
    print("Press CTRL+C to stop the server")
    app.run(host="0.0.0.0", port=5000, debug=True)
