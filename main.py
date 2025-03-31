import csv
import os
import requests
import re
from urllib.parse import urlparse

def sanitize_filename(name):
    # Remove invalid characters for filenames
    name = re.sub(r'[\/*?:"<>|]', "", name)
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    # Truncate long names if necessary (optional)
    return name[:100] # Keep filename length reasonable

def download_image(url, filepath):
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes

        # Check content type to make sure it's an image and get extension
        content_type = response.headers.get('content-type')
        if not content_type or not content_type.startswith('image'):
            print(f"Skipping non-image URL: {url} (Content-Type: {content_type})")
            return None

        # Try to get a valid extension
        path = urlparse(url).path
        _, ext = os.path.splitext(path)
        if not ext or len(ext) > 5: # Basic check for valid extension
             # Fallback based on content type
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'webp' in content_type:
                ext = '.webp'
            elif 'gif' in content_type:
                 ext = '.gif'
            else:
                print(f"Skipping URL with unknown image type: {url} (Content-Type: {content_type})")
                return None # Skip if we can't determine a reasonable extension

        filepath_with_ext = f"{filepath}{ext}"

        with open(filepath_with_ext, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {filepath_with_ext}")
        return filepath_with_ext # Return the final filename with extension
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None

def main():
    csv_filename = 'amcouch.csv'
    output_folder = 'product_images'

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created folder: {output_folder}")

    try:
        with open(csv_filename, 'r', encoding='utf-8') as csvfile:
            # Handle potential BOM (Byte Order Mark) if present
            if csvfile.read(1) != '\ufeff':
                csvfile.seek(0)
            reader = csv.reader(csvfile)
            header = next(reader) # Skip header row

            # Find column indices dynamically (more robust)
            try:
                product_name_col = header.index('Product name')
                image_cols = [
                    header.index('Image 1 Link'),
                    header.index('Image 2 Link'),
                    header.index('Image 3 Link'),
                    header.index('Image 4 Link'),
                    header.index('Image 5 Link')
                ]
            except ValueError as e:
                print(f"Error: Missing required column in CSV header - {e}")
                return

            for i, row in enumerate(reader):
                 # Handle rows with fewer columns than expected gracefully
                try:
                    product_name = row[product_name_col].strip()
                    if not product_name:
                        print(f"Skipping row {i+2}: Empty product name.")
                        continue

                    sanitized_name = sanitize_filename(product_name)
                    image_count = 0
                    for j, col_index in enumerate(image_cols):
                         # Check if column index is valid for the current row
                        if col_index < len(row):
                            image_url = row[col_index].strip()
                            if image_url and image_url.lower() not in ['na', 'n/a']:
                                image_count += 1
                                base_filepath = os.path.join(output_folder, f"{sanitized_name}_{image_count}")
                                download_image(image_url, base_filepath)
                        else:
                             print(f"Skipping image {j+1} for product '{product_name}' (Row {i+2}): Column index {col_index} out of range for row length {len(row)}.")

                except IndexError:
                     print(f"Skipping row {i+2}: Not enough columns.")
                except Exception as e:
                    print(f"Error processing row {i+2} for product '{product_name}': {e}")


    except FileNotFoundError:
        print(f"Error: CSV file '{csv_filename}' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
