import requests
import os
from datetime import datetime

groupOrderUrl = "https://api.rapidprinttee.com/api/vendor/admin/group-order"
groupOrdersParams = {
    'page': 1,
    'pageSize': 100
}

headers = {
    'X-Access-Key': '66aee1fcf80a9fc2becb9482:vPytvV2LYHcg0s3GM5jV7bGW5jBRwzH0xPuF'
}


def fetch_group_print_images(group_id):
    url = f"https://api.rapidprinttee.com/api/vendor/admin/group-order/{group_id}/print-images"
    
    response = requests.get(url, headers=headers)
    
    # Return the response data or an error message
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed with status code {response.status_code}", "details": response.text}

# Fetch the entire dictionary
def fetch_print_images_base_group_order(group_order_list):
    print_image_base_group_order_dict= {}
    
    for group_order_id in group_order_list:
        response_data = fetch_group_print_images(group_order_id)
        print_image_base_group_order_dict[group_order_id] = response_data

    return print_image_base_group_order_dict



def fetch_latest_group_order_list():
    try:
        response = requests.get(groupOrderUrl, headers=headers, params=groupOrdersParams)
        response.raise_for_status()  # Raise an error if the request was not successful
        
        # Parse the JSON data
        parsed_data = response.json()

        # Get the "dataTable"
        data_table = parsed_data['data']['dataTable']

        # Current day in the format of YYYY-MM-DD
        current_day = datetime.now().strftime('%Y-%m-%d')
        #current_day = '2024-08-28'
        # Iterate through the data_table and find entries where the createdAt date is the same as today
        latest_group_orders_list = []
        for entry in data_table:
            created_at = entry['createdAt'].split("T")[0]
            if created_at == current_day:
                latest_group_orders_list.append(entry['code'])
        
        return latest_group_orders_list
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return []
    
def download_image(url, file_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded {file_path}")
        else:
            print(f"Failed to download {url}")
    except Exception as e:
        print(f"Exception occurred while downloading {url}: {e}")

def create_folders_and_download_images(data_dict, base_path):
    os.makedirs(base_path, exist_ok=True)  # Create base path if it does not exist
    for group, content in data_dict.items():
        if content["code"] == 0:
            group_folder = os.path.join(base_path, group)
            os.makedirs(group_folder, exist_ok=True)
            for item in content["data"]:
                folder_name = item["folder_name"].strip()
                for folder in item["folders"]:
                    side = folder.get("side", "").strip()
                    side_folder = os.path.join(group_folder, folder_name, side) if side else os.path.join(group_folder, folder_name)
                    os.makedirs(side_folder, exist_ok=True)
                    for file in folder.get("files", []):
                        file_name = file["file_name"].strip()
                        url = file["url"].strip()
                        file_path = os.path.join(side_folder, file_name)
                        download_image(url, file_path)

# if __name__ == "__main__":
#     group_order_list = fetch_latest_group_order_list()
#     data_dict = fetch_print_images_base_group_order(group_order_list)
#     base_path = "processed_order" 
#     create_folders_and_download_images(data_dict, base_path)