from PIL import Image, ImageDraw, ImageFont, ImageFile
from rectpack import newPacker, SORT_AREA, PackingMode
import os
import logging

Image.MAX_IMAGE_PIXELS = None

def crop_image(input_image_path, output_image_path, margin, dpi):
    image = Image.open(input_image_path)

    # Pillow's cropping box is in left, upper, right, lower pixel coordinates
    image_data = image.getdata()

    # Get bounding box
    bbox = image_data.getbbox()

    # Generate new bounding box with margin
    bbox_with_margin = [bbox[0] - margin, bbox[1] - margin, bbox[2] + margin, bbox[3] + margin]

    # Precautionary measures to prevent negative cropping values
    bbox_with_margin = [max(0, bbox_val) for bbox_val in bbox_with_margin]

    # Crop the image to the contents of the bounding box
    cropped_image = image.crop(bbox_with_margin)

    # Save the cropped image
    cropped_image.save(output_image_path, dpi=(dpi, dpi))

def resize_image(input_image_path, output_image_path, max_width_inches, max_height_inches, dpi, margin):
    # Open the original image
    original_image = Image.open(input_image_path)

    #crop image
    # Pillow's cropping box is in left, upper, right, lower pixel coordinates
    image_data = original_image.getdata()
    bbox = image_data.getbbox()
    bbox_with_margin = [bbox[0] - margin, bbox[1] - margin, bbox[2] + margin, bbox[3] + margin]
    bbox_with_margin = [max(0, bbox_val) for bbox_val in bbox_with_margin]
    cropped_image = original_image.crop(bbox_with_margin)

    original_width, original_height = cropped_image.size

    # Convert max_width from inches to pixels
    target_width_pixels = round(max_width_inches * dpi)
    max_height_pixels = round(max_height_inches * dpi)

    # If original width is smaller than target width, just return.
    if original_width < target_width_pixels:
        target_width_pixels = original_width

    # Calculate the aspect ratio of the original image
    aspect_ratio = original_height / original_width

    # Calculate the target height to maintain the original aspect ratio
    target_height_pixels = round(target_width_pixels * aspect_ratio)

    #limit the height to max height
    if target_height_pixels > max_height_pixels:
        # Calculate the aspect ratio of the original image
        target_height_pixels = max_height_pixels
        aspect_ratio2 = target_width_pixels / target_height_pixels
        target_width_pixels = round(target_height_pixels*aspect_ratio2)

    # Resize the image maintaining the aspect ratio
    resized_image = cropped_image.resize((target_width_pixels, target_height_pixels), Image.LANCZOS)

    # Save the resized image
    resized_image.save(output_image_path, dpi=(dpi, dpi))
    logging.info(f"Image resize to {target_width_pixels} x {target_height_pixels} pixel with dpi {dpi}")

class Paper:
    def __init__(self, width_inches, dpi):
        self.width = round(width_inches * dpi)

def pack_and_combine_images(input_image_folder, output_image_path, paper_width_size_in, dpi, image_file_failed):
    # Initialize a Paper with the max_width_inches and dpi
    paper = Paper(paper_width_size_in, dpi)

    # List to store (image_path, width, height) tuples.
    image_sizes = []

    for file_name in os.listdir(input_image_folder):
        image_path = os.path.join(input_image_folder, file_name)
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                image_sizes.append((image_path, width, height))
        except Exception as e:
            logging.error(f"File {file_name} is corrupted. SKipping")
            image_file_failed.add(os.path.splitext(file_name)[0])

    packer = newPacker(rotation=True, sort_algo=SORT_AREA, mode=PackingMode.Offline )

    for image_path, w, h in image_sizes:
        packer.add_rect(w, h, image_path)  # image_path rightly used as rectangle id


    # Add a bin with the width of the 'Paper'
    max_height = 1e6
    packer.add_bin(paper.width, max_height)

    # Start packing
    packer.pack()

    # Full bin list
    all_rects = packer.rect_list()

    if not all_rects:
        logging.error("No images were packed!")
        return

    # Prepare the canvas to paste the images
    total_height = max([y+h for b, x, y, w, h, rid in all_rects])
    final_img = Image.new('RGBA', (paper.width, total_height), (0, 0, 0, 0))

    # Paste each image into the final image according to calculated (x, y) positions
    for rect in all_rects:
        b, x, y, w, h, rid = rect
        img = Image.open(rid)
        img_w, img_h = img.size
        if img_w != w and img_h != h:
            img = img.transpose(Image.ROTATE_90) 

        final_img.paste(img, (x, y))

    # Save the final image
    final_img.save(output_image_path, dpi=(dpi, dpi))

#the only way to check for if an image is a logo is to see if it is smaller than a certain size
#size_inches=(width_inches, height_inches)
def check_image_is_logo(input_image_path, size_inches, dpi):
    width_pixels, height_pixels = size_inches[0] * dpi, size_inches[1] * dpi
    original_image = Image.open(input_image_path)
    w, h = original_image.size
    return w<=width_pixels and h<=height_pixels

def add_text_to_existing_image(input_path,above_text, below_text, output_path):
    # Open the existing image
    font_size = 72
    text_color = "black"
    original_image = Image.open(input_path)

    # Get the image dimensions
    width, height = original_image.size

    # Calculate the new height to accommodate text above and below
    new_height = height + 2 * font_size + 30  # Adjust as needed
    new_image = Image.new("RGBA", (width, new_height), (0, 0, 0, 0))

    # Paste the original image in the middle of the new image
    new_image.paste(original_image, (0, font_size + 10))

    # Create a drawing object
    draw = ImageDraw.Draw(new_image)

    # Choose a font (you need to have a font file on your system)
    font = ImageFont.load_default()
    font = ImageFont.load_default().font_variant(size=font_size)

    # # Position to center the text above
    x_above = 0
    y_above = 5  # Adjust as needed

    # Draw the text above the image
    draw.text((x_above, y_above), above_text, font=font, fill=text_color)

    x_below = 0
    y_below = height + font_size + 15  # Adjust as needed

    # # Draw the text below the image
    draw.text((x_below, y_below), below_text, font=font, fill=text_color)

    # Save the new image to a file
    new_image.save(output_path)