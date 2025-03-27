from flask_login import LoginManager
from database import db, User

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def init_users():
    """
    This function only ensures user flags are set correctly.
    It does NOT modify passwords - those should be set using the setup.py script.
    """
    # User data without passwords
    users = [{
        'username': 'anya', 'can_edit': True, 'is_family': True
    }, {
        'username': 'nucc', 'can_edit': True, 'is_family': True
    }, {
        'username': 'vivi', 'can_edit': True, 'is_family': True
    }, {
        'username': 'gergo', 'can_edit': True, 'is_family': True
    }, {
        'username': 'guest', 'can_edit': False, 'is_family': False
    }, {
        'username': 'family_guest', 'can_edit': False, 'is_family': True
    }]

    for user_data in users:
        user = User.query.filter_by(username=user_data['username']).first()
        if user:
            # Update existing users with proper flags
            user.can_edit = user_data['can_edit']
            user.is_family = user_data['is_family']

    db.session.commit()
