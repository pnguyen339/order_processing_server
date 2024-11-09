from image_processing import pack_and_combine_images, add_text_to_existing_image, resize_image
from logging_config import setup_logging
from order_pictures_fectching import create_folders_and_download_images, fetch_latest_group_order_list, fetch_print_images_base_group_order
import multiprocessing
import logging
import os
import time
import shutil
from datetime import datetime, timedelta

def delete_old_files_and_folders(folder_path):
    # Calculate the cutoff date (two weeks ago from today)
    cutoff_date = datetime.now() - timedelta(weeks=2)
    
    # Iterate over all items in the specified folder
    for item_name in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item_name)
        
        # Get the creation time of the item
        creation_time = os.path.getctime(item_path)
        creation_date = datetime.fromtimestamp(creation_time)
        
        # Check if the item is older than two weeks and delete accordingly
        if creation_date < cutoff_date:
            if os.path.isfile(item_path):
                os.remove(item_path)
                print(f"Deleted file: {item_path}")
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print(f"Deleted directory: {item_path}")

def process_check_for_new_order(shared_path, next_process_work_queue):
    setup_logging()

    process_name = multiprocessing.current_process().name
    logging.info(f"Process Check for New Group Order ID:{process_name}")

    while True:
        try:
            logging.info("Checking to see if there is new group order")
            group_order_list = fetch_latest_group_order_list()
            
            for group_order_id in group_order_list:
                dir_path = os.path.join(shared_path, group_order_id)
                if not os.path.exists(dir_path):
                    new_group_order_id_list = []
                    logging.info(f"Proccessing Group Order ID {group_order_id}")
                    new_group_order_id_list.append(group_order_id)
                    data_dict = fetch_print_images_base_group_order(new_group_order_id_list)
                    create_folders_and_download_images(data_dict, shared_path)
                    next_process_work_queue.put(group_order_id)

            #Return this script every 5 minutes
            delete_old_files_and_folders(shared_path)
            time.sleep(5*60)  
        except KeyboardInterrupt:
            logging.info(f"Process one received KeyboardInterrupt. Exiting...")
        except Exception as e:
            time.sleep(60)
            logging.error(f"Process one failed. Restarting due to {e}")

def process_and_combine_images(next_process_work_queue, max_width_size, dpi, margin, shared_path, max_num_images):
    setup_logging()
     # Get the current process name or process ID
    process_name = multiprocessing.current_process().name
    logging.info(f"Process and Combine Images-Process ID:{process_name}")

    # Folders to ignore
    ignore_substring = 'Resize Images'
    fixed_ignore_folders = {'All White'}

    resize_images_folder_name = "Resize Images"
    try:
        while True:
            if not next_process_work_queue.empty():
                group_order_id = next_process_work_queue.get()
                group_order_id_folder_path = os.path.join(shared_path, group_order_id)
                num_of_imgs = 0
                split_num = 0
                resize_images_folder_path = os.path.join(group_order_id_folder_path, f'{resize_images_folder_name}_Split_{split_num}')
                os.makedirs(resize_images_folder_path, exist_ok=True)
                for folder_name in os.listdir(group_order_id_folder_path):
                    folder_path = os.path.join(group_order_id_folder_path, folder_name)
                    if os.path.isdir(folder_path) and folder_name not in fixed_ignore_folders and ignore_substring not in folder_name:
                        try:
                            # Extract the size WxH from the folder name
                            size_str = folder_name.split()[-1]
                            max_width, max_height = map(float, size_str.split('x'))
                            
                            for folder_name_2 in os.listdir(folder_path):
                                folder_name_2_path = os.path.join(folder_path, folder_name_2)
                                # Process each image in the directory
                                for img_name in os.listdir(folder_name_2_path):
                                    img_path = os.path.join(folder_name_2_path, img_name)
                                    if os.path.isfile(img_path):
                                        output_img_path = os.path.join(resize_images_folder_path, img_name)
                                        resize_image(img_path, output_img_path, max_width, max_height, dpi, margin)
                                        num_of_imgs= num_of_imgs + 1
                                        if num_of_imgs >= max_num_images:
                                            png_filename = f"Combined_Images_{group_order_id}_Split_{split_num}.png"
                                            png_filename_path = os.path.join(group_order_id_folder_path, png_filename)
                                            image_file_failed = set()
                                            pack_and_combine_images(resize_images_folder_path, png_filename_path, max_width_size, dpi, image_file_failed)
                                            above_text = f'{group_order_id}: {png_filename}------Split {split_num}'
                                            below_text = f'{group_order_id}------Split {split_num}: {num_of_imgs - len(image_file_failed)} pictures printed. {len(image_file_failed)} pictures failed'
                                            add_text_to_existing_image(png_filename_path, above_text , below_text, png_filename_path)
                                            split_num = split_num + 1
                                            resize_images_folder_path = os.path.join(group_order_id_folder_path, f'{resize_images_folder_name}_Split_{split_num}')
                                            os.makedirs(resize_images_folder_path, exist_ok=True)
                                            num_of_imgs=0

                        except Exception as e:
                            logging.error(f"Error processing folder {folder_name}: {e}")

                #Combine all the images into a single file
                png_filename = f"Combined_Images_{group_order_id}_Split_{split_num}.png"
                png_filename_path = os.path.join(group_order_id_folder_path, png_filename)
                image_file_failed = set()
                pack_and_combine_images(resize_images_folder_path, png_filename_path, max_width_size, dpi, image_file_failed)
                above_text = f'{group_order_id}: {png_filename}------Split {split_num}'
                below_text = f'{group_order_id}------Split {split_num}: {num_of_imgs - len(image_file_failed)} pictures printed. {len(image_file_failed)} pictures failed'
                add_text_to_existing_image(png_filename_path, above_text , below_text, png_filename_path)
            
            time.sleep(5 * 60)
    except KeyboardInterrupt:
        logging.info(f"Process two received KeyboardInterrupt. Exiting...")

# if __name__ == "__main__":
#      dest_folder = "processed_order"
#      next_process_work_queue = multiprocessing.Queue()
#      process_check_for_new_order(dest_folder, next_process_work_queue)
#      #next_process_work_queue.put("GROUP0000000443")
#      process_and_combine_images(next_process_work_queue, 22, 300, .5, dest_folder, 20)