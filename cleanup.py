import os
import time
from datetime import datetime, timedelta

# Folder Paths
OUTPUT_FOLDER = os.path.join('temp', 'outputs')

def cleanup_files():
    print("Cleanup process started...")
    # 1 ghanta purani files delete karein
    cutoff_time = datetime.utcnow() - timedelta(hours=1)
    
    count = 0
    if os.path.exists(OUTPUT_FOLDER):
        for filename in os.listdir(OUTPUT_FOLDER):
            file_path = os.path.join(OUTPUT_FOLDER, filename)
            # File ka creation time check karein
            file_mtime = datetime.utcfromtimestamp(os.path.getmtime(file_path))
            
            if file_mtime < cutoff_time:
                os.remove(file_path)
                count += 1
    
    print(f"Cleanup finished. {count} files removed.")

if __name__ == "__main__":
    cleanup_files()