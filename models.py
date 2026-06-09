from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    # 'owner' aur 'author' ka use karein taake conflict na ho
    files = db.relationship('FileHistory', backref='owner', lazy=True, cascade='all, delete-orphan')
    feedbacks = db.relationship('Feedback', backref='author', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class FileHistory(db.Model):
    __tablename__ = 'file_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_name = db.Column(db.String(100))
    operation_type = db.Column(db.String(50))
    file_path = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
class Feedback(db.Model):
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer)
    comment = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship yahan wapas define karne ki zaroorat nahi hai 
    # kyunki User class mein 'feedbacks' aur 'author' backref handle ho raha hai.