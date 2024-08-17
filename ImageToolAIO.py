import os
from PIL import Image, PngImagePlugin

def get_user_input(prompt):
    user_input = input(prompt).strip().lower()
    if user_input not in ['y', 'yes', 'n', 'no']:
        return 'no'
    return user_input

def display_help():
    help_message = """
    This script processes images in a specified directory. It can crop images, remove or retain metadata, 
    save in a different format, compress, resize, and add metadata. It applies these operations to all images 
    in the directory without needing confirmation for each file.
    """
    print(help_message)

def crop_image(img, crop_percent, crop_position):
    width, height = img.size
    crop_amount_width = int((crop_percent / 100.0) * width)
    crop_amount_height = int((crop_percent / 100.0) * height)
    
    if crop_position == 'top':
        return img.crop((0, crop_amount_height, width, height))
    elif crop_position == 'bottom':
        return img.crop((0, 0, width, height - crop_amount_height))
    elif crop_position == 'left':
        return img.crop((crop_amount_width, 0, width, height))
    elif crop_position == 'right':
        return img.crop((0, 0, width - crop_amount_width, height))

def handle_metadata(img, img_path, keep_metadata, format):
    exif_bytes = None
    if format == 'jpeg' and keep_metadata:
        import piexif
        exif_dict = piexif.load(img_path)
        exif_bytes = piexif.dump(exif_dict)
    elif format == 'png' and keep_metadata:
        metadata = img.info
        exif_bytes = {k: v for k, v in metadata.items() if k.startswith('exif')}
    return exif_bytes

def save_image(img, path, format, exif_bytes=None):
    if exif_bytes and format == 'jpeg':
        import piexif
        img.save(path, format=format, exif=exif_bytes)
    else:
        img.save(path, format=format)

def process_images(directory, crop_percent, crop_position, keep_metadata, save_format, compress, resize, resize_percent, add_metadata):
    formats = ('.png', '.jpg', '.jpeg', '.webp')
    total_files = 0
    total_space_saved = 0

    for filename in os.listdir(directory):
        if filename.lower().endswith(formats):
            total_files += 1
            filepath = os.path.join(directory, filename)
            img = Image.open(filepath)
            original_size = os.path.getsize(filepath)
            original_format = img.format.lower()

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

            if compress:
                try:
                    img = Image.open(new_filepath)
                    img.save(new_filepath, optimize=True, quality=85)
                except Exception as e:
                    print(f"Error compressing {new_filepath}: {e}")
                    continue

            if resize:
                try:
                    img = Image.open(new_filepath)
                    width, height = img.size
                    new_dimensions = (int(width * resize_percent / 100), int(height * resize_percent / 100))
                    img = img.resize(new_dimensions)
                    save_image(img, new_filepath, save_format, exif_bytes)
                except Exception as e:
                    print(f"Error resizing {new_filepath}: {e}")
                    continue

            if add_metadata and not keep_metadata:
                try:
                    img = Image.open(new_filepath)
                    if save_format == 'png':
                        meta_data = PngImagePlugin.PngInfo()
                        if 'author' in add_metadata:
                            meta_data.add_text("Author", add_metadata['author'])
                        if 'keyword' in add_metadata:
                            meta_data.add_text("Keyword", add_metadata['keyword'])
                        if 'copyright' in add_metadata:
                            meta_data.add_text("Copyright", add_metadata['copyright'])
                        img.save(new_filepath, pnginfo=meta_data)
                    else:
                        # Adding metadata for JPEG or other formats can be done here if necessary
                        pass
                except Exception as e:
                    print(f"Error adding metadata to {new_filepath}: {e}")
                    continue

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
        
        resize = get_user_input("Resize images? (yes/no): ") in ['y', 'yes']
        resize_percent = 100
        if resize:
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

        process_images(directory, crop_percent, crop_position, keep_metadata, save_format, compress, resize, resize_percent, add_metadata)
