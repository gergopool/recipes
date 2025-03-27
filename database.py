from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    can_edit = db.Column(db.Boolean, default=False)
    is_family = db.Column(db.Boolean, default=False)  # New flag for family members

    def set_password(self, password):
        # Increase the security by using a stronger method and more iterations
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256:100000')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)  # Keep for backward compatibility
    memory = db.Column(db.Text, nullable=True)  # New memory field
    category = db.Column(db.String(20), nullable=False)  # Soup, main_dish, desert, other
    main_image = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Add explicit user relationship
    user = db.relationship('User', foreign_keys=[user_id])

    ingredients = db.relationship('Ingredient',
                                  backref='recipe',
                                  lazy='dynamic',
                                  cascade='all, delete-orphan')
    steps = db.relationship('Step', backref='recipe', lazy='dynamic', cascade='all, delete-orphan')


class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.String(50))
    unit = db.Column(db.String(20))  # gram, kávéskanál, etc.
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))


class Step(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(100))
    order = db.Column(db.Integer)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))


class FamilyPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer)  # Just store the year
    description = db.Column(db.Text)
