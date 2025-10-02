#!/usr/bin/env python3
"""
Cleanup utility for Smart Attendance System
Removes temporary files and reduces clutter
"""

import os
import glob
import time
from pathlib import Path

def cleanup_temp_files():
    """Clean up temporary files older than 1 hour."""
    temp_patterns = [
        "*.tmp",
        "*.temp", 
        "temp_*",
        "*_temp",
        "tmp_*",
        "*_tmp"
    ]
    
    cleaned_count = 0
    current_time = time.time()
    one_hour_ago = current_time - 3600  # 1 hour in seconds
    
    for pattern in temp_patterns:
        for file_path in glob.glob(pattern):
            try:
                if os.path.isfile(file_path):
                    file_age = os.path.getmtime(file_path)
                    if file_age < one_hour_ago:
                        os.remove(file_path)
                        cleaned_count += 1
                        print(f"Cleaned: {file_path}")
            except Exception as e:
                print(f"Error cleaning {file_path}: {e}")
    
    return cleaned_count

def cleanup_old_backups():
    """Clean up old backup files older than 7 days."""
    backup_patterns = [
        "*.enc",
        "*.bak",
        "*.backup"
    ]
    
    cleaned_count = 0
    current_time = time.time()
    seven_days_ago = current_time - (7 * 24 * 3600)  # 7 days in seconds
    
    for pattern in backup_patterns:
        for file_path in glob.glob(pattern):
            try:
                if os.path.isfile(file_path):
                    file_age = os.path.getmtime(file_path)
                    if file_age < seven_days_ago:
                        os.remove(file_path)
                        cleaned_count += 1
                        print(f"Cleaned old backup: {file_path}")
            except Exception as e:
                print(f"Error cleaning {file_path}: {e}")
    
    return cleaned_count

def cleanup_data_directory():
    """Clean up the data directory."""
    data_dir = Path("data")
    if not data_dir.exists():
        return 0
    
    cleaned_count = 0
    
    # Clean up temporary files in data directory
    for temp_file in data_dir.glob("*.tmp"):
        try:
            temp_file.unlink()
            cleaned_count += 1
            print(f"Cleaned data temp: {temp_file}")
        except Exception as e:
            print(f"Error cleaning {temp_file}: {e}")
    
    return cleaned_count

def main():
    """Main cleanup function."""
    print("🧹 Smart Attendance System Cleanup")
    print("=" * 40)
    
    # Clean up temporary files
    print("Cleaning temporary files...")
    temp_cleaned = cleanup_temp_files()
    print(f"Cleaned {temp_cleaned} temporary files")
    
    # Clean up old backups
    print("\nCleaning old backup files...")
    backup_cleaned = cleanup_old_backups()
    print(f"Cleaned {backup_cleaned} old backup files")
    
    # Clean up data directory
    print("\nCleaning data directory...")
    data_cleaned = cleanup_data_directory()
    print(f"Cleaned {data_cleaned} data temporary files")
    
    total_cleaned = temp_cleaned + backup_cleaned + data_cleaned
    print(f"\n✅ Total files cleaned: {total_cleaned}")
    
    if total_cleaned == 0:
        print("✨ System is already clean!")

if __name__ == "__main__":
    main()
