from PIL import Image
import os
from config import Config
from werkzeug.utils import secure_filename
import uuid


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def process_image(file,
                  target_folder,
                  size=(800, 800),
                  thumbnail_size=(300, 300),
                  square_crop=False):
    """
    Process uploaded images:
    - Convert to jpg
    - Resize to max dimensions
    - Create thumbnail version
    - Create square cropped version if requested
    
    Returns the filename of the processed image
    """
    if file and allowed_file(file.filename):
        # Create a unique filename to avoid collisions
        filename = str(uuid.uuid4()) + '.jpg'

        # Make sure the target folder exists
        os.makedirs(target_folder, exist_ok=True)

        filepath = os.path.join(target_folder, filename)

        # Save and convert to JPG
        img = Image.open(file)
        img = img.convert('RGB')

        # Resize while maintaining aspect ratio
        img.thumbnail(size, Image.Resampling.LANCZOS)
        img.save(filepath, 'JPEG', quality=85)

        # Create thumbnail
        thumb = img.copy()
        thumb.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
        thumb_path = os.path.join(target_folder, 'thumb_' + filename)
        thumb.save(thumb_path, 'JPEG', quality=85)

        # Create square crop (from center)
        if square_crop:
            # Calculate dimensions
            width, height = img.size
            crop_size = min(width, height)
            left = (width - crop_size) // 2
            top = (height - crop_size) // 2
            right = left + crop_size
            bottom = top + crop_size

            # Crop and save
            square = img.crop((left, top, right, bottom))
            square.thumbnail((100, 100), Image.Resampling.LANCZOS)  # Resize to smaller square
            square_path = os.path.join(target_folder, 'square_' + filename)
            square.save(square_path, 'JPEG', quality=85)

        return filename
    return None


def process_family_photo(file, target_folder, original_size=(1600, 1600),
                         thumbnail_size=(300, 300)):
    """
    Process uploaded family photos:
    - Resize to reasonable dimensions while preserving aspect ratio
    - Create thumbnail version for gallery view
    
    Returns the filename of the processed image
    """
    if file and allowed_file(file.filename):
        # Create a unique filename to avoid collisions
        filename = str(uuid.uuid4()) + '.jpg'
        filepath = os.path.join(target_folder, filename)

        # Create family photos folder if it doesn't exist
        family_folder = os.path.join(target_folder, 'family')
        if not os.path.exists(family_folder):
            os.makedirs(family_folder)

        filepath = os.path.join(family_folder, filename)

        # Save and convert to JPG
        img = Image.open(file)
        img = img.convert('RGB')

        # Resize while maintaining aspect ratio
        img.thumbnail(original_size, Image.Resampling.LANCZOS)
        img.save(filepath, 'JPEG', quality=85)

        # Create thumbnail
        thumb = img.copy()
        thumb.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
        thumb_path = os.path.join(family_folder, 'thumb_' + filename)
        thumb.save(thumb_path, 'JPEG', quality=85)

        return filename
    return None


def cleanup_orphaned_images(app):
    """Finds and removes image files that have no database references.
    Only deletes files that are definitely orphaned."""
    from database import Recipe, Step, FamilyPhoto
    import os

    print("Starting orphaned image cleanup...")

    # Create sets of all referenced images
    recipe_images = set()
    step_images = set()
    family_photos = set()

    # Collect all recipe main images
    for recipe in Recipe.query.all():
        if recipe.main_image:
            recipe_images.add(recipe.main_image)
            recipe_images.add('thumb_' + recipe.main_image)

    # Collect all step images
    for step in Step.query.all():
        if step.image:
            step_images.add(step.image)
            step_images.add('square_' + step.image)

    # Collect all family photos
    for photo in FamilyPhoto.query.all():
        if photo.filename:
            family_photos.add(photo.filename)
            family_photos.add('thumb_' + photo.filename)

    print(
        f"Found {len(recipe_images)} recipe images, {len(step_images)} step images, and {len(family_photos)} family photos referenced in database"
    )

    # Check main uploads folder for orphaned recipe and step images
    uploads_folder = app.config['UPLOAD_FOLDER']
    removed_count = 0
    skipped_count = 0

    # Process files in the main uploads folder
    if os.path.exists(uploads_folder):
        for filename in os.listdir(uploads_folder):
            file_path = os.path.join(uploads_folder, filename)

            # Skip directories and special files
            if os.path.isdir(file_path) or filename == '.gitkeep':
                continue

            # Only process jpg/png files for safety
            if not (filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg') or
                    filename.lower().endswith('.png')):
                skipped_count += 1
                continue

            # Check if file is referenced
            if filename not in recipe_images and filename not in step_images:
                # Extra safety check - see if it's a thumbnail or square file
                if filename.startswith('thumb_') and filename[6:] in recipe_images:
                    continue
                if filename.startswith('square_') and filename[7:] in step_images:
                    continue

                # File is definitely not referenced
                try:
                    # Just log what would be deleted for first run
                    print(f"Removing orphaned image: {filename}")
                    os.remove(file_path)
                    removed_count += 1
                except Exception as e:
                    print(f"Error removing {filename}: {e}")
            else:
                print(f"Keeping referenced image: {filename}")

    # Process files in the family photos subfolder
    family_folder = os.path.join(uploads_folder, 'family')
    if os.path.exists(family_folder):
        for filename in os.listdir(family_folder):
            file_path = os.path.join(family_folder, filename)

            # Skip directories and special files
            if os.path.isdir(file_path) or filename == '.gitkeep':
                continue

            # Only process jpg/png files for safety
            if not (filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg') or
                    filename.lower().endswith('.png')):
                skipped_count += 1
                continue

            # Check if file is referenced in family photos
            if filename not in family_photos:
                # Extra safety check for thumbnails
                if filename.startswith('thumb_') and filename[6:] in family_photos:
                    continue

                # File is definitely not referenced
                try:
                    print(f"Removing orphaned family photo: {filename}")
                    os.remove(file_path)
                    removed_count += 1
                except Exception as e:
                    print(f"Error removing family photo {filename}: {e}")
            else:
                print(f"Keeping referenced family photo: {filename}")

    print(
        f"Cleanup complete. Removed {removed_count} orphaned images. Skipped {skipped_count} non-image files."
    )
    return removed_count
