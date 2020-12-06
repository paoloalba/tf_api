from sqlalchemy import UniqueConstraint
from flask_user import UserMixin
from . import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), nullable=False, unique=True)
    email_confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(255), nullable=False, server_default='')
    name = db.Column(db.String(100))

    # Define the relationship to Role via UserRoles
    roles = db.relationship('Role', secondary='user_roles')

    current_game = db.Column(db.String(100))

    @property
    def roles_names(self):
        if self.roles:
            return [rrr.name for rrr in self.roles]
        else:
            return []
    @property
    def is_admin(self):
        if self.roles:
            return "Admin" in self.roles_names
        else:
            return False

# Define the Role data-model
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

# Define the UserRoles association table
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer(), primary_key=True)

    name = db.Column(db.String(50), nullable=False)

    step = db.Column(db.Integer(), nullable=False)
    step_at = db.Column(db.DateTime())

    rule = db.Column(db.String(50))
    phase = db.Column(db.String(50), nullable=False)
    player = db.Column(db.String(50))

    image_is_saved = db.Column(db.Boolean())
    detected_cards = db.Column(db.String(50))

    requested_for = db.relationship('User', secondary='game_users')
    requested_for_email = db.Column(db.String(100), nullable=False)

    __table_args__ = (UniqueConstraint('name', 'step', 'requested_for_email', name='_name_step_usermail'),
                     )

class GameUsers(db.Model):
    __tablename__ = 'game_users'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    game_id = db.Column(db.Integer(), db.ForeignKey('games.id', ondelete='CASCADE'))
