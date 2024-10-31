import os

from datetime import datetime
from flask import render_template, request, redirect, flash, url_for, session
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from .config import *
from .db import *


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def context_processor():
    return dict(is_admin=is_admin)


###MAIN PAGES###

@app.route('/')
def index():
    tours = Tour.query.order_by(Tour.available_spots.asc()).limit(3).all()
    return render_template('index.html', tours=tours)


@app.route('/search', methods=['GET'])
def search_results():
    search = request.args.get('search')
    if search:
        tours = Tour.query.filter(
            (Tour.name.contains(search) | Tour.description.contains(search)) &
            (Tour.available_spots > 0)
        ).all()
    else:
        tours = []

    return render_template('search_results.html', tours=tours, search=search)


@app.route('/tours/')
def tours():
    # Start with the base query
    query = Tour.query

    # Apply filters based on query parameters
    price_max = request.args.get('price_max')
    date = request.args.get('date')
    available_spots_min = request.args.get('available_spots_min')

    if price_max:
        query = query.filter(Tour.price_per_person <= float(price_max))
    if date:
        query = query.filter(Tour.date == date)
    if available_spots_min:
        query = query.filter(Tour.available_spots >= int(available_spots_min))

    # Execute query and render the page with filtered tours
    tours = query.all()
    return render_template('tours.html', tours=tours)


@app.route('/tour/<int:id>')
def tour_detail(id):
    tour = Tour.query.get_or_404(id)
    return render_template('tour_detail.html', tour=tour)


@app.route('/book_tour/<int:id>', methods=['GET', 'POST'])
@login_required
def book_tour(id):
    tour = Tour.query.get_or_404(id)

    if request.method == 'POST':
        num_people = int(request.form.get('num_people'))
        total_price = num_people * tour.price_per_person

        if num_people > tour.available_spots:
            flash('Недостатньо місць!')
            return redirect(url_for('book_tour', id=id))

        booking = Booking(user_id=current_user.id, tour_id=tour.id, num_people=num_people, total_price=total_price)

        tour.available_spots -= num_people
        db.session.add(booking)
        db.session.commit()

        flash(f'Бронювання успішне! Загальна ціна: {total_price}')
        return redirect(url_for('profile'))

    return render_template('book_tour.html', tour=tour)


@app.route('/cancel_booking/<int:id>', methods=['POST'])
@login_required
def cancel_booking(id):
    booking = Booking.query.get_or_404(id)

    if booking.user_id != current_user.id:
        flash('You cannot cancel this booking.', 'danger')
        return redirect(url_for('profile'))

    tour = Tour.query.get(booking.tour_id)
    tour.available_spots += booking.num_people

    db.session.delete(booking)
    db.session.commit()

    flash('Your booking has been cancelled and spots have been returned!', 'success')
    return redirect(url_for('profile'))


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
        )

        db.session.add(new_tour)
        db.session.commit()
        flash('Tour added successfully!')
        return redirect(url_for('index'))

    return render_template('add_tour.html')


@app.route('/search')
def search():
    filters = request.args.to_dict()
    search_query = filters.get('search', '')
    query = Tour.query

    if search_query:
        query = query.filter(
            (Tour.name.contains(search_query) | Tour.description.contains(search_query)) &
            (Tour.available_spots > 0)
        )

    tours = query.all()
    return render_template('index.html', tours=tours)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if User.query.filter_by(username=username).first():
            error = 'Username already exists. Please choose a different one.'
            return render_template('register.html', error=error)

        if User.query.filter_by(email=email).first():
            error = 'Email already registered. Please use a different one.'
            return render_template('register.html', error=error)

        if password != confirm_password:
            error = 'Passwords do not match. Please try again.'
            return render_template('register.html', error=error)

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
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password. Please try again.'
            return render_template('login.html', error=error)

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', user=current_user, bookings=user_bookings)


@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_new_password = request.form.get('confirm_new_password')

    if not check_password_hash(current_user.password_hash, old_password):
        flash('Old password is incorrect.', 'danger')
        return redirect(url_for('profile'))

    if new_password != confirm_new_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('profile'))

    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    flash('Password successfully changed!', 'success')
    return redirect(url_for('profile'))


def is_admin(user_id):
    admin_ids = [1]
    return user_id in admin_ids


@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))

    tours = Tour.query.all()
    return render_template('admin_panel.html', tours=tours)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/edit_tour/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_tour(id):
    tour = Tour.query.get_or_404(id)
    if request.method == 'POST':
        tour.name = request.form.get('name')
        tour.description = request.form.get('description')
        tour.price_per_person = request.form.get('price_per_person')
        # Convert date string to date object
        date_str = request.form.get('date')
        if date_str:
            tour.date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Convert available_spots to integer
        available_spots_str = request.form.get('available_spots')
        if available_spots_str:
            tour.available_spots = int(available_spots_str)

        # Handle photo upload
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                photo.save(os.path.join(UPLOAD_FOLDER, filename))
                tour.image_path = filename

        db.session.commit()
        flash('Tour updated successfully!', 'success')
        return redirect(url_for('admin_panel'))

    return render_template('edit_tour.html', tour=tour)

@app.route('/delete_tour/<int:id>')
def delete_tour(id):
    tour = Tour.query.get_or_404(id)
    db.session.delete(tour)
    db.session.commit()
    flash('Tour deleted successfully!', 'success')
    return redirect(url_for('admin_panel'))
