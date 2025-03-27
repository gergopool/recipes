from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
from flask_login import login_user, logout_user, login_required, current_user
from database import db, Recipe, Ingredient, Step, User, FamilyPhoto
from auth import login_manager, init_users, User
from utils import process_image, process_family_photo, cleanup_orphaned_images
from config import Config
import os
import json
import random
from flask import session

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)

# Set the login view for the login_required decorator
login_manager.login_view = 'login'

# Create database tables and users
with app.app_context():
    db.create_all()
    init_users()


# Example user creation code
def create_default_users():
    if User.query.count() == 0:
        admin = User(username="admin", can_edit=True)
        admin_password = os.environ.get('ADMIN_PASSWORD', 'your-admin-password')
        admin.set_password(admin_password)

        user1 = User(username="user1", can_edit=True)
        user1_password = os.environ.get('USER1_PASSWORD', 'user1-password')
        user1.set_password(user1_password)

        # Add more users as needed

        db.session.add_all([admin, user1])
        db.session.commit()


# Import translations (you'll edit this file)
@app.context_processor
def inject_translations():
    # Load translations from the JSON file
    with open('translations/hu.json', 'r', encoding='utf-8') as f:
        translations = json.load(f)
    return dict(translations=translations)


def get_translations():
    with open('translations/hu.json', 'r', encoding='utf-8') as f:
        return json.load(f)


@app.route('/')
def index():
    # Redirect to login if not authenticated, otherwise to browse
    if current_user.is_authenticated:
        return redirect(url_for('browse'))
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, go to browse
    if current_user.is_authenticated:
        return redirect(url_for('browse'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            # Redirect to the page they were trying to access or browse
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('browse'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session['_flashes'] = []
    logout_user()
    translations = get_translations()
    flash(translations['logout_success'], category='info')
    return redirect(url_for('login'))


@app.route('/browse')
@login_required  # Add login_required to all routes
def browse():
    search = request.args.get('search', '')
    category = request.args.get('category', '')

    query = Recipe.query.outerjoin(User)

    if search:
        query = query.filter(Recipe.title.ilike(f'%{search}%'))
    if category and category != 'all':
        query = query.filter(Recipe.category == category)

    recipes = query.order_by(Recipe.created_at.desc()).all()
    return render_template('browse.html', recipes=recipes)


@app.route('/recipes/<int:recipe_id>')
@login_required
def recipe_detail(recipe_id):
    recipe = Recipe.query.outerjoin(User).filter(Recipe.id == recipe_id).first_or_404()

    if recipe.user_id and not recipe.user:
        recipe.user = User.query.get(recipe.user_id)

    # Get a random family photo if the user is a family member
    random_family_photo = None
    if current_user.is_family:
        # Check if there are any family photos
        photo_count = FamilyPhoto.query.count()
        if photo_count > 0:
            # Get a random photo
            random_index = random.randint(0, photo_count - 1)
            random_family_photo = FamilyPhoto.query.offset(random_index).limit(1).first()

    return render_template('recipe_detail.html',
                           recipe=recipe,
                           random_family_photo=random_family_photo)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_recipe():
    if not current_user.can_edit:
        return redirect(url_for('browse'))

    if request.method == 'POST':
        recipe = Recipe(title=request.form['title'],
                        memory=request.form['memory'],
                        category=request.form['category'],
                        user_id=current_user.id)

        # Process main image
        if 'main_image' in request.files:
            file = request.files['main_image']
            if file.filename != '':
                image_path = process_image(file, app.config['UPLOAD_FOLDER'], square_crop=True)
                if image_path:
                    recipe.main_image = os.path.basename(image_path)

        db.session.add(recipe)
        db.session.commit()

        # Process ingredients
        for i in range(len(request.form.getlist('ingredient_name'))):
            name = request.form.getlist('ingredient_name')[i]
            amount = request.form.getlist('ingredient_amount')[i]
            unit = request.form.getlist('ingredient_unit')[i]

            if name:  # Only add if there's a name
                ingredient = Ingredient(name=name, amount=amount, unit=unit, recipe_id=recipe.id)
                db.session.add(ingredient)

        # Process steps
        for i, step_desc in enumerate(request.form.getlist('step_description')):
            if step_desc:  # Only add if there's a description
                step = Step(description=step_desc, order=i + 1, recipe_id=recipe.id)

                # Process step image if exists
                step_key = f'step_image_{i}'
                if step_key in request.files:
                    file = request.files[step_key]
                    if file.filename != '':
                        image_path = process_image(file,
                                                   app.config['UPLOAD_FOLDER'],
                                                   square_crop=True)
                        if image_path:
                            step.image = os.path.basename(image_path)
                            print(
                                f"DEBUG: Step image processed and saved as: {os.path.basename(image_path)}"
                            )
                            print(
                                f"DEBUG: Square thumbnail should be at: square_{os.path.basename(image_path)}"
                            )

                db.session.add(step)

        db.session.commit()
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))

    return render_template('upload.html')


@app.route('/recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    # Check if user can edit
    if not current_user.can_edit:
        return redirect(url_for('browse'))

    # Additional debug prints
    print(f"DEBUG: Editing recipe {recipe_id}")
    recipe = Recipe.query.get_or_404(recipe_id)

    if request.method == 'GET':
        print(f"DEBUG: Main image: {recipe.main_image}")
        for step in recipe.steps:
            print(f"DEBUG: Step {step.order} image: {step.image}")
            if step.image:
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], step.image)
                square_path = os.path.join(app.config['UPLOAD_FOLDER'], f"square_{step.image}")
                print(f"DEBUG: Full path exists: {os.path.exists(full_path)}")
                print(f"DEBUG: Square path exists: {os.path.exists(square_path)}")

    if request.method == 'POST':
        recipe.title = request.form['title']
        recipe.memory = request.form['memory']
        recipe.category = request.form['category']

        # Process main image (handle new uploads or deletions)
        if 'remove_main_image' in request.form and request.form['remove_main_image'] == '1':
            # User wants to delete the main image
            if recipe.main_image:
                try:
                    # Delete the image files
                    main_path = os.path.join(app.config['UPLOAD_FOLDER'], recipe.main_image)
                    thumb_path = os.path.join(app.config['UPLOAD_FOLDER'],
                                              'thumb_' + recipe.main_image)

                    if os.path.exists(main_path):
                        os.remove(main_path)
                    if os.path.exists(thumb_path):
                        os.remove(thumb_path)

                    recipe.main_image = None
                except Exception as e:
                    print(f"Error deleting main image: {e}")

        # Process new main image if uploaded
        if 'main_image' in request.files:
            file = request.files['main_image']
            if file and file.filename != '':
                image_path = process_image(file, app.config['UPLOAD_FOLDER'], square_crop=False)
                if image_path:
                    # Delete old image if it exists
                    if recipe.main_image:
                        try:
                            old_path = os.path.join(app.config['UPLOAD_FOLDER'], recipe.main_image)
                            old_thumb = os.path.join(app.config['UPLOAD_FOLDER'],
                                                     'thumb_' + recipe.main_image)
                            if os.path.exists(old_path):
                                os.remove(old_path)
                            if os.path.exists(old_thumb):
                                os.remove(old_thumb)
                        except Exception as e:
                            print(f"Error deleting old main image: {e}")

                    recipe.main_image = os.path.basename(image_path)

        # Process ingredients
        # Delete existing ingredients
        for ingredient in recipe.ingredients:
            db.session.delete(ingredient)

        # Add new ingredients
        for i in range(len(request.form.getlist('ingredient_name'))):
            name = request.form.getlist('ingredient_name')[i]
            amount = request.form.getlist('ingredient_amount')[i]
            unit = request.form.getlist('ingredient_unit')[i]

            if name:  # Only add if there's a name
                ingredient = Ingredient(name=name, amount=amount, unit=unit, recipe_id=recipe.id)
                db.session.add(ingredient)

        # Handle steps - delete existing steps first
        for step in recipe.steps:
            db.session.delete(step)

        # Add new steps from form
        step_descriptions = []
        step_files = []

        # Collect step data from the form
        for key, value in request.form.items():
            if key.startswith('step_description_'):
                step_index = int(key.split('_')[-1])
                step_descriptions.append((step_index, value))

        # Sort by index to maintain order
        step_descriptions.sort(key=lambda x: x[0])

        # Create new Step objects
        for i, (_, description) in enumerate(step_descriptions):
            step = Step(description=description, order=i + 1, recipe=recipe)

            # Check if there's an image for this step
            step_image_key = f'step_image_{i}'
            if step_image_key in request.files and request.files[step_image_key].filename:
                image_file = request.files[step_image_key]
                filename = process_image(image_file,
                                         os.path.join(app.config['UPLOAD_FOLDER']),
                                         square_crop=True)
                step.image = filename

            db.session.add(step)

        db.session.commit()
        translations = get_translations()
        flash(translations['recipe_updated'], 'success')
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))

    return render_template('edit_recipe.html', recipe=recipe)


# Family photo routes
@app.route('/family/photos')
@login_required
def family_photos():
    # Check if user is family member
    if not current_user.is_family:
        flash('Access restricted to family members')
        return redirect(url_for('browse'))

    photos = FamilyPhoto.query.order_by(FamilyPhoto.year.desc()).all()
    return render_template('family_photos.html', photos=photos)


@app.route('/family/upload_photo', methods=['GET', 'POST'])
@login_required
def upload_family_photo():
    # Check if user is family member
    if not current_user.is_family:
        flash('You do not have permission to upload photos')
        return redirect(url_for('family_photos'))

    if request.method == 'POST':
        year = request.form.get('year', '')
        description = request.form.get('description', '')

        # Convert year to integer
        try:
            year = int(year) if year else None
        except ValueError:
            year = None

        if 'photo' in request.files:
            file = request.files['photo']
            if file.filename != '':
                filename = process_family_photo(file, app.config['UPLOAD_FOLDER'])

                if filename:
                    photo = FamilyPhoto(filename=filename, year=year, description=description)
                    db.session.add(photo)
                    db.session.commit()
                    flash('Photo uploaded successfully!')
                    return redirect(url_for('family_photos'))

        flash('Please select a photo to upload')

    return render_template('upload_family_photo.html')


@app.route('/family/edit_photo/<int:photo_id>', methods=['GET', 'POST'])
@login_required
def edit_family_photo(photo_id):
    # Check if user is family member and can edit
    if not current_user.is_family or not current_user.can_edit:
        flash('You do not have permission to edit photos')
        return redirect(url_for('family_photos'))

    photo = FamilyPhoto.query.get_or_404(photo_id)

    if request.method == 'POST':
        year = request.form.get('year', '')
        description = request.form.get('description', '')

        # Convert year to integer
        try:
            photo.year = int(year) if year else None
        except ValueError:
            photo.year = None

        photo.description = description
        db.session.commit()
        translations = get_translations()
        flash(translations['photo_updated'], 'info')
        return redirect(url_for('family_photos'))

    return render_template('edit_family_photo.html', photo=photo)


@app.route('/family/delete_photo/<int:photo_id>', methods=['POST'])
@login_required
def delete_family_photo(photo_id):
    # Check if user is family member and can edit
    if not current_user.is_family or not current_user.can_edit:
        flash('You do not have permission to delete photos')
        return redirect(url_for('family_photos'))

    photo = FamilyPhoto.query.get_or_404(photo_id)

    # Delete the image files too
    try:
        # Get the paths to the image files
        base_path = app.config['UPLOAD_FOLDER']
        family_folder = os.path.join(base_path, 'family')
        file_path = os.path.join(family_folder, photo.filename)
        thumb_path = os.path.join(family_folder, 'thumb_' + photo.filename)

        # Delete the files if they exist
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
    except Exception as e:
        print(f"Error deleting files: {e}")

    # Delete from database
    db.session.delete(photo)
    db.session.commit()

    # Run cleanup after photo deletion
    cleanup_orphaned_images(app)

    translations = get_translations()
    flash(translations['photo_deleted'], 'success')
    return redirect(url_for('family_photos'))


@app.route('/delete-recipe/<int:recipe_id>', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    # Check if user can edit
    if not current_user.can_edit:
        flash('Nincs jogosultságod a receptek törléséhez.')
        return redirect(url_for('browse'))

    recipe = Recipe.query.get_or_404(recipe_id)

    # Delete associated ingredients
    Ingredient.query.filter_by(recipe_id=recipe.id).delete()

    # Delete associated steps
    # First get all steps to find images to delete
    steps = Step.query.filter_by(recipe_id=recipe.id).all()
    for step in steps:
        if step.image:
            # Delete step images if they exist
            try:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], step.image)
                square_path = os.path.join(app.config['UPLOAD_FOLDER'], 'square_' + step.image)

                if os.path.exists(image_path):
                    os.remove(image_path)
                if os.path.exists(square_path):
                    os.remove(square_path)
            except Exception as e:
                print(f"Error deleting step image: {e}")

    # Delete all steps
    Step.query.filter_by(recipe_id=recipe.id).delete()

    # Delete main image if it exists
    if recipe.main_image:
        try:
            main_path = os.path.join(app.config['UPLOAD_FOLDER'], recipe.main_image)
            thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumb_' + recipe.main_image)

            if os.path.exists(main_path):
                os.remove(main_path)
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        except Exception as e:
            print(f"Error deleting main image: {e}")

    # Delete the recipe
    db.session.delete(recipe)
    db.session.commit()

    # Run cleanup after recipe deletion
    cleanup_orphaned_images(app)

    translations = get_translations()
    flash(translations['recipe_deleted'], 'success')
    return redirect(url_for('browse'))


# Add this route to serve protected images
@app.route('/protected_media/<path:filename>')
@login_required
def protected_media(filename):
    """Serve protected media files only to authenticated users"""

    # Security: Validate filename to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        abort(404)

    # Check if the file exists in the upload folder
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.isfile(file_path):
        abort(404)

    # Determine the file's directory
    directory = os.path.dirname(file_path)
    base_filename = os.path.basename(filename)

    # Serve the file to the authenticated user
    return send_from_directory(directory, base_filename)


# For family photos, add extra check to verify user is family member
@app.route('/protected_family_media/<path:filename>')
@login_required
def protected_family_media(filename):
    """Serve family media files only to family members"""

    if not current_user.is_family:
        abort(403)  # Forbidden

    # Security: Validate filename to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        abort(404)

    # Check if the file exists in the upload folder - family subfolder
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'family', filename)
    if not os.path.isfile(file_path):
        abort(404)

    # Serve the file to the authenticated family member
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'family'), filename)


if __name__ == '__main__':
    with app.app_context():
        print("Running initial image cleanup...")
        cleanup_orphaned_images(app)
    app.run(host='0.0.0.0', port=5000, debug=True)
