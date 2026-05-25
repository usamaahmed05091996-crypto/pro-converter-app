import os
import time
import logging

# Logging configure karein taake pata chale kya ho raha hai
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

FOLDERS_TO_CLEAN = ['temp/uploads', 'temp/outputs']
AGE_LIMIT_SECONDS = 3600  # 1 Ghanta

def clean_temp_files():
    """Folders se 1 ghante purani files ko remove karein."""
    current_time = time.time()
    
    for folder in FOLDERS_TO_CLEAN:
        if not os.path.exists(folder):
            logging.warning(f"Folder not found, skipping: {folder}")
            continue
            
        logging.info(f"Scanning folder: {folder}")
        
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            
            # .gitkeep ya hidden files ko touch na karein
            if filename.startswith('.'): continue
            
            try:
                if os.path.isfile(file_path):
                    file_age = os.path.getmtime(file_path)
                    
                    if (current_time - file_age) > AGE_LIMIT_SECONDS:
                        os.remove(file_path)
                        logging.info(f"Successfully deleted: {filename}")
            except Exception as e:
                logging.error(f"Failed to delete {filename}: {str(e)}")

if __name__ == "__main__":
    logging.info("Starting automated cleanup process...")
    try:
        clean_temp_files()
        logging.info("Cleanup process finished successfully.")
    except Exception as e:
        logging.critical(f"Cleanup script crashed: {str(e)}")