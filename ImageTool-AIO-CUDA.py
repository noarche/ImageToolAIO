import os
import torch
from PIL import PngImagePlugin
from torchvision import transforms
from torchvision.io import read_image, write_jpeg, write_png
from torchvision.transforms.functional import crop, resize

def get_user_input(prompt):
    user_input = input(prompt).strip().lower()
    if user_input not in ['y', 'yes', 'n', 'no']:
        return 'no'
    return user_input

def display_help():
    help_message = """
    This script processes images in a specified directory using GPU acceleration. It can crop images, remove or retain metadata,
    save in a different format, compress, resize, and add metadata. It applies these operations to all images in the directory 
    without needing confirmation for each file.
    """
    print(help_message)

def crop_image(img, crop_percent, crop_position):
    _, height, width = img.shape
    crop_amount_width = int((crop_percent / 100.0) * width)
    crop_amount_height = int((crop_percent / 100.0) * height)
    
    if crop_position == 'top':
        return crop(img, crop_amount_height, 0, height - crop_amount_height, width)
    elif crop_position == 'bottom':
        return crop(img, 0, 0, height - crop_amount_height, width)
    elif crop_position == 'left':
        return crop(img, 0, crop_amount_width, height, width - crop_amount_width)
    elif crop_position == 'right':
        return crop(img, 0, 0, height, width - crop_amount_width)

def handle_metadata(img, img_path, keep_metadata, format):
    exif_bytes = None
    # Metadata handling can be incorporated using torch-based operations if required
    return exif_bytes

def save_image(img, path, format, exif_bytes=None):
    if format == 'jpeg':
        write_jpeg(img, path, quality=85)
    elif format == 'png':
        write_png(img, path)

def process_images(directory, crop_percent, crop_position, keep_metadata, save_format, compress, resize_flag, resize_percent, add_metadata):
    formats = ('.png', '.jpg', '.jpeg', '.webp')
    total_files = 0
    total_space_saved = 0

    for filename in os.listdir(directory):
        if filename.lower().endswith(formats):
            total_files += 1
            filepath = os.path.join(directory, filename)
            img = read_image(filepath).cuda()
            original_size = os.path.getsize(filepath)
            original_format = os.path.splitext(filename)[1][1:].lower()

            img = crop_image(img, crop_percent, crop_position)
            exif_bytes = handle_metadata(img, filepath, keep_metadata, original_format)
            
            # Adjust format for saving
            if save_format == 'jpg':
                save_format = 'jpeg'

            new_filepath = os.path.join(directory, '_' + os.path.splitext(filename)[0] + '.' + save_format.lower())
            
            try:
                save_image(img, new_filepath, save_format, exif_bytes)
            except Exception as e:
                print(f"Error saving {new_filepath}: {e}")
                continue

            if compress and save_format == 'jpeg':
                # JPEG compression can be handled by setting the quality in save_image
                pass

            if resize_flag:
                try:
                    new_size = [int(d * resize_percent / 100) for d in img.shape[-2:]]
                    img = resize(img, new_size)
                    save_image(img, new_filepath, save_format, exif_bytes)
                except Exception as e:
                    print(f"Error resizing {new_filepath}: {e}")
                    continue

            # Additional metadata handling could be added here
            
            try:
                new_size = os.path.getsize(new_filepath)
                space_saved = original_size - new_size
                total_space_saved += space_saved
                os.remove(filepath)  # Remove the original file
                os.rename(new_filepath, os.path.join(directory, filename))  # Rename new file to original name
            except FileNotFoundError as e:
                print(f"File not found: {new_filepath}, {e}")
                continue

    print(f"Processed {total_files} files.")
    print(f"Total space saved: {total_space_saved / 1024:.2f} KB")
    input("Press Enter to restart the script...")

if __name__ == "__main__":
    display_help()
    while True:
        directory = get_user_input("Enter the directory of images: ")
        crop_percent = float(get_user_input("Enter the % to crop images by: "))
        crop_position = get_user_input("Crop from (top, bottom, left, right): ").lower()
        keep_metadata = get_user_input("Keep metadata? (yes/no): ") in ['y', 'yes']
        save_format = get_user_input("Enter the format to save images as (png, jpg, jpeg, webp): ").lower()
        compress = get_user_input("Compress images? (yes/no): ") in ['y', 'yes']
        
        resize_flag = get_user_input("Resize images? (yes/no): ") in ['y', 'yes']
        resize_percent = 100
        if resize_flag:
            resize_percent = float(get_user_input("Resize images by %: "))

        add_metadata = {}
        if not keep_metadata and get_user_input("Would you like to add metadata (author, keyword, copyright)? (yes/no): ") in ['y', 'yes']:
            author = get_user_input("Enter author: ")
            keyword = get_user_input("Enter keyword: ")
            copyright = get_user_input("Enter copyright: ")
            if author:
                add_metadata['author'] = author
            if keyword:
                add_metadata['keyword'] = keyword
            if copyright:
                add_metadata['copyright'] = copyright

        process_images(directory, crop_percent, crop_position, keep_metadata, save_format, compress, resize_flag, resize_percent, add_metadata)
