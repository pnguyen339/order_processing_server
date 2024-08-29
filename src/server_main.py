import configparser
import multiprocessing
import signal
import sys
import os
import time
from scripts_process import process_check_for_new_order, process_and_combine_images
import logging
from logging_config import setup_logging

# Default config
DESTINATION_FOLDER = "processed_order"
DPI = 300
MARGIN = 50  # pixel
MAX_WIDTH_SIZE = 24  # inches
MAX_ORDERS_PER_PRINT = 20
NUMBER_OF_PROCESSES_FOR_1 = 1
NUMBER_OF_PROCESSES_FOR_2 = 2
LOGGING_DESTINATION = "log"

def read_config():
    # Instantiate the ConfigParser object then read the file
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Accessing the values in the configuration file
    # PRINT_SETTING config
    global DESTINATION_FOLDER, DPI, MARGIN, MAX_WIDTH_SIZE, MAX_ORDERS_PER_PRINT, NUMBER_OF_PROCESSES_FOR_1, NUMBER_OF_PROCESSES_FOR_2, LOGGING_DESTINATION
    DESTINATION_FOLDER = str(config.get('PRINT_SETTING', 'DESTINATION_FOLDER'))
    os.makedirs(DESTINATION_FOLDER, exist_ok=True)
    DPI = int(config.get('PRINT_SETTING', 'DPI'))
    MARGIN = int(config.get('PRINT_SETTING', 'MARGIN'))
    MAX_WIDTH_SIZE = int(config.get('PRINT_SETTING', 'MAX_WIDTH_SIZE'))
    MAX_ORDERS_PER_PRINT = int(config.get('PRINT_SETTING', 'MAX_ORDERS_PER_PRINT'))
    NUMBER_OF_PROCESSES_FOR_2 = int(config.get('SERVER_SETTING', 'NUMBER_OF_PROCESSES_FOR_PROCESS_2'))
    NUMBER_OF_PROCESSES_FOR_1 = int(config.get('SERVER_SETTING', 'NUMBER_OF_PROCESSES_FOR_PROCESS_1'))
    LOGGING_DESTINATION = str(config.get('SERVER_SETTING', 'LOGGING_DESTINATION'))

if __name__ == "__main__":
    next_process_work_queue = multiprocessing.Queue()

    read_config()
    setup_logging(LOGGING_DESTINATION)
    processes = []

    for _ in range(NUMBER_OF_PROCESSES_FOR_1):
        process_one_worker = multiprocessing.Process(target=process_check_for_new_order,
                                                     args=(DESTINATION_FOLDER, next_process_work_queue))
        processes.append(process_one_worker)

    for _ in range(NUMBER_OF_PROCESSES_FOR_2):
        process_two_worker = multiprocessing.Process(target=process_and_combine_images,
                                                     args=(next_process_work_queue, MAX_WIDTH_SIZE, DPI, MARGIN, DESTINATION_FOLDER, MAX_ORDERS_PER_PRINT))
        processes.append(process_two_worker)

    try:
        # Create and start each process
        for process in processes:
            process.start()
            time.sleep(10)

        # Wait for keyboard interrupt
        signal.pause()
    except KeyboardInterrupt:
        logging.info("Main process received KeyboardInterrupt. Stopping all processes...")

        # Terminate all processes
        for process in processes:
            process.terminate()
            process.join()

        logging.info("All processes stopped. Exiting...")
        sys.exit(0)