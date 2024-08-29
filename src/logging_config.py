import logging
import os
import multiprocessing
from datetime import datetime

CURRENT_LOG_PATH = "log"

def setup_logging(log_path=None):
    global CURRENT_LOG_PATH
    if log_path != None:
        CURRENT_LOG_PATH = log_path
    
    if not os.path.exists(CURRENT_LOG_PATH):
        os.makedirs(CURRENT_LOG_PATH)

    # Create a file handler and set the log file path
    # Create a log file with a timestamp
    process_id = multiprocessing.current_process().name
    log_filename = os.path.join(CURRENT_LOG_PATH, f"log_{process_id}_{datetime.now().strftime('%Y%m%d')}.log")

    file_handler = logging.FileHandler(log_filename)
    
    # Set up the log format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(processName)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add the file handler to the root logger
    logging.getLogger().addHandler(file_handler)
    
    # Set the logging level
    logging.getLogger().setLevel(logging.INFO)