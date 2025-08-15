from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    total_points = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    preferred_language = db.Column(db.String(2), default='ar')  # 'ar' or 'en'
    
    # علاقات
    daily_points = db.relationship('DailyPoints', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)
    user_images = db.relationship('UserImage', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can_use_advanced_titles(self):
        return self.total_points >= 200

    def can_use_image_feature(self):
        return self.total_points >= 500

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'total_points': self.total_points,
            'is_admin': self.is_admin,
            'preferred_language': self.preferred_language,
            'can_use_advanced_titles': self.can_use_advanced_titles(),
            'can_use_image_feature': self.can_use_image_feature()
        }

class DailyPoints(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tool_name = db.Column(db.String(50), nullable=False)  # 'smart_titles', 'tasks', 'smart_emoji'
    points_earned = db.Column(db.Integer, default=25)
    date_earned = db.Column(db.Date, default=date.today)
    
    # فهرس مركب لضمان عدم تكرار النقاط لنفس الأداة في نفس اليوم
    __table_args__ = (db.UniqueConstraint('user_id', 'tool_name', 'date_earned'),)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'tool_name': self.tool_name,
            'points_earned': self.points_earned,
            'date_earned': self.date_earned.isoformat()
        }

class Tool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    description_ar = db.Column(db.Text)
    description_en = db.Column(db.Text)
    is_free = db.Column(db.Boolean, default=True)
    required_points = db.Column(db.Integer, default=0)
    daily_points_reward = db.Column(db.Integer, default=25)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_ar': self.name_ar,
            'name_en': self.name_en,
            'description_ar': self.description_ar,
            'description_en': self.description_en,
            'is_free': self.is_free,
            'required_points': self.required_points,
            'daily_points_reward': self.daily_points_reward,
            'is_active': self.is_active
        }

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title_ar = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)
    content_ar = db.Column(db.Text, nullable=False)
    content_en = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # علاقات
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title_ar': self.title_ar,
            'title_en': self.title_en,
            'content_ar': self.content_ar,
            'content_en': self.content_en,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'comments_count': len(self.comments)
        }

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'user_id': self.user_id,
            'username': self.user.username,
            'post_id': self.post_id,
            'created_at': self.created_at.isoformat(),
            'is_approved': self.is_approved
        }

class UserImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime, nullable=False)  # تاريخ انتهاء العرض (يوم واحد)
    is_approved = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username,
            'image_path': self.image_path,
            'upload_date': self.upload_date.isoformat(),
            'expiry_date': self.expiry_date.isoformat(),
            'is_approved': self.is_approved,
            'is_active': self.is_active
        }

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
