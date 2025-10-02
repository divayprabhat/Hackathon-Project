"""
Smart Attendance System Launcher
Simple launcher for non-technical users with splash screen
"""

import sys
import os
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser
import time
from cleanup import cleanup_temp_files


def check_requirements():
    """Check if required packages are installed."""
    try:
        import cv2, dlib, numpy, pandas, flask
        from PIL import Image
        return True
    except ImportError as e:
        return False, str(e)


def install_requirements():
    """Install required packages."""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )
        return True
    except subprocess.CalledProcessError:
        return False


def start_server(server_file="run_server.py", https=False):
    """Start the Flask server in background."""
    try:
        if https:
            subprocess.Popen([sys.executable, server_file])
            webbrowser.open("https://127.0.0.1:5000")
        else:
            subprocess.Popen([sys.executable, server_file])
            webbrowser.open("http://127.0.0.1:5000")
        return True
    except Exception as e:
        print("Server failed to start:", e)
        return False


def show_splash():
    """Display splash screen with progress bar."""
    splash = tk.Toplevel()
    splash.title("Loading Smart Attendance System")
    splash.geometry("400x120")
    splash.resizable(False, False)

    tk.Label(splash, text="Smart Attendance System",
             font=("Segoe UI", 14, "bold")).pack(pady=10)
    progress = ttk.Progressbar(splash, mode="indeterminate", length=300)
    progress.pack(pady=10)
    progress.start(10)  # speed of animation

    # Center the splash on screen
    splash.update_idletasks()
    x = (splash.winfo_screenwidth() // 2) - (400 // 2)
    y = (splash.winfo_screenheight() // 2) - (120 // 2)
    splash.geometry(f"+{x}+{y}")

    return splash, progress


def main():
    """Main launcher function."""
    root = tk.Tk()
    root.withdraw()  # Hide main window

    if not os.path.exists("main.py"):
        messagebox.showerror("Error", "Please run this from the attendance system directory!")
        return

    # Cleanup
    print("Cleaning up temporary files...")
    try:
        cleanup_temp_files()
    except Exception:
        pass

    # Check requirements
    print("Checking requirements...")
    req_check = check_requirements()
    if not req_check:
        print("Installing requirements...")
        if not install_requirements():
            messagebox.showerror(
                "Error",
                "Failed to install requirements. Please run: pip install -r requirements.txt"
            )
            return

    # User choice
    choice = messagebox.askyesnocancel(
        "Smart Attendance System",
        "Welcome to Smart Attendance System!\n\n"
        "Choose your option:\n"
        "• YES - Start Desktop App (Recommended)\n"
        "• NO - Start Web Interface\n"
        "• CANCEL - Exit"
    )

    if choice is None:
        return

    elif choice:  # Desktop App
        try:
            print("Starting Desktop App with splash...")
            splash, progress = show_splash()
            root.after(200, lambda: root.update())  # keep splash responsive

            # Start main.py in background
            proc = subprocess.Popen([sys.executable, "main.py"])
            time.sleep(2)  # show splash for at least 2 seconds
            splash.destroy()

            proc.wait()  # Wait until GUI is closed

            # After GUI closes → start Flask server automatically
            print("Desktop App closed. Starting Flask server...")
            if start_server("server.py", https=False):
                messagebox.showinfo("Info", "Web server started automatically after closing the desktop app.")
            else:
                messagebox.showerror("Error", "Failed to start web server after closing the desktop app.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start desktop app: {e}")

    else:  # Web Interface
        https_choice = messagebox.askyesno(
            "Web Interface Options",
            "Choose web interface type:\n\n"
            "• YES - HTTPS (Secure, Recommended)\n"
            "• NO - HTTP (Standard)"
        )
        try:
            if https_choice:
                print("Starting HTTPS Web Server...")
                try:
                    subprocess.run([sys.executable, "generate_ssl_cert.py"], check=True)
                except subprocess.CalledProcessError:
                    print("Warning: Could not generate SSL certificates")
                if start_server("server_https.py", https=True):
                    messagebox.showinfo("Success", "HTTPS Web interface opened in browser.")
                else:
                    messagebox.showerror("Error", "Failed to start HTTPS web server!")
            else:
                print("Starting HTTP Web Server...")
                if start_server("server.py", https=False):
                    messagebox.showinfo("Success", "Web interface opened in browser.")
                else:
                    messagebox.showerror("Error", "Failed to start web server!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start web interface: {e}")


if __name__ == "__main__":
    main()
