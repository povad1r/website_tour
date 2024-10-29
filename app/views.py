import os

from flask import render_template, request, redirect, flash, url_for
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from .db import *


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
###MAIN PAGES###

@app.route('/')
def index():
    search = request.args.get('search')
    if search:
        tours = Tour.query.filter(
            (Tour.name.contains(search) | Tour.description.contains(search)) &
            (Tour.available_spots > 0)  # Only include tours with available spots
        ).all()
    else:
        tours = Tour.query.filter(Tour.available_spots > 0).all()  # Only include tours with available spots
    return render_template('index.html', tours=tours)

@app.route('/tours/', methods=['GET'])
def tours():
    tours = Tour.query.filter(Tour.available_spots > 0).all()  # Only include tours with available spots
    return render_template('tours.html', tours=tours)  # Передати тури в шаблон

# Сторінка деталей туру
@app.route('/tour/<int:id>')
def tour_detail(id):
    tour = Tour.query.get_or_404(id)
    return render_template('tour_detail.html', tour=tour)

# Сторінка бронювання
@app.route('/book_tour/<int:id>', methods=['GET', 'POST'])
def book_tour(id):
    tour = Tour.query.get_or_404(id)
    if request.method == 'POST':
        num_people = int(request.form.get('num_people'))
        total_price = num_people * tour.price_per_person

        if num_people > tour.available_spots:
            flash('Недостатньо місць!')  # Not enough spots available
            return redirect(url_for('book_tour', id=id))

        tour.available_spots -= num_people
        db.session.commit()
        flash(f'Бронювання успішне! Загальна ціна: {total_price}')  # Booking successful!
        return redirect(url_for('index'))

    return render_template('book_tour.html', tour=tour)



# Панель адміністратора (доступ тільки для адміністраторів)
@app.route('/add_tour', methods=['GET', 'POST'])
def add_tour():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price_per_person = float(request.form['price_per_person'])
        date_str = request.form['date']
        available_spots = int(request.form['available_spots'])

        date = datetime.strptime(date_str, '%Y-%m-%d').date()

        image = request.files['image']
        image_path = f"uploads/{image.filename}"
        image.save(os.path.join(app.root_path, 'static', image_path))

        new_tour = Tour(
            name=name,
            description=description,
            price_per_person=price_per_person,
            date=date,
            available_spots=available_spots,
            image_path=image_path
            # creation_time будет автоматически установлен
        )

        db.session.add(new_tour)
        db.session.commit()
        flash('Tour added successfully!')
        return redirect(url_for('index'))

    return render_template('add_tour.html')
@app.route('/search')
def search():
    filters = request.args.to_dict()
    query = Tour.query
    if 'price_min' in filters:
        query = query.filter(Tour.price_per_person >= float(filters['price_min']))
    if 'price_max' in filters:
        query = query.filter(Tour.price_per_person <= float(filters['price_max']))
    # Додаткові фільтри
    tours = query.all()
    return render_template('index.html', tours=tours)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use a different one.')
            return redirect(url_for('register'))

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.')

    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)