from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from flask_login import UserMixin

from .config import *


db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(80), nullable=False)


class Tour(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creation_time = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price_per_person = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    available_spots = db.Column(db.Integer, nullable=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tour_id = db.Column(db.Integer, db.ForeignKey('tour.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    num_people = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    user = db.relationship('User', backref=db.backref('bookings', lazy=True))
    tour = db.relationship('Tour', backref=db.backref('bookings', lazy=True))