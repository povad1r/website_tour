import os

from flask import render_template, request, redirect, flash, url_for, session
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
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
    tours = Tour.query.filter(Tour.available_spots > 0).all()
    return render_template('index.html', tours=tours)

@app.route('/search', methods=['GET'])
def search_results():
    search = request.args.get('search')
    if search:
        tours = Tour.query.filter(
            (Tour.name.contains(search) | Tour.description.contains(search)) &
            (Tour.available_spots > 0)  # Only include tours with available spots
        ).all()
    else:
        tours = []  # No search term provided, return an empty list

    return render_template('search_results.html', tours=tours, search=search)
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
@login_required  # Ensure the user is logged in
def book_tour(id):
    tour = Tour.query.get_or_404(id)

    if request.method == 'POST':
        num_people = int(request.form.get('num_people'))
        total_price = num_people * tour.price_per_person

        # Check if enough spots are available
        if num_people > tour.available_spots:
            flash('Недостатньо місць!')  # Not enough spots available
            return redirect(url_for('book_tour', id=id))

        # Create a new booking
        booking = Booking(user_id=current_user.id, tour_id=tour.id, num_people=num_people, total_price=total_price)

        # Update available spots and add the booking
        tour.available_spots -= num_people
        db.session.add(booking)  # Add the booking to the session
        db.session.commit()  # Commit the changes

        flash(f'Бронювання успішне! Загальна ціна: {total_price}')  # Booking successful!
        return redirect(url_for('index'))  # Redirect to a relevant page

    return render_template('book_tour.html', tour=tour)


@app.route('/cancel_booking/<int:id>', methods=['POST'])
@login_required
def cancel_booking(id):
    booking = Booking.query.get_or_404(id)

    # Ensure the current user is the owner of the booking
    if booking.user_id != current_user.id:
        flash('You cannot cancel this booking.', 'danger')
        return redirect(url_for('profile'))  # Redirect to the profile page

    # Increase available spots in the tour
    tour = Tour.query.get(booking.tour_id)
    tour.available_spots += booking.num_people

    # Delete the booking
    db.session.delete(booking)
    db.session.commit()

    flash('Your booking has been cancelled and spots have been returned!', 'success')
    return redirect(url_for('profile'))  # Redirect to the profile page

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
    search_query = filters.get('search', '')
    query = Tour.query

    if search_query:
        query = query.filter(
            (Tour.name.contains(search_query) | Tour.description.contains(search_query)) &
            (Tour.available_spots > 0)  # Only include tours with available spots
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

        # Check if the username or email already exists
        if User.query.filter_by(username=username).first():
            error = 'Username already exists. Please choose a different one.'
            return render_template('register.html', error=error)

        if User.query.filter_by(email=email).first():
            error = 'Email already registered. Please use a different one.'
            return render_template('register.html', error=error)

        # Check if passwords match
        if password != confirm_password:
            error = 'Passwords do not match. Please try again.'
            return render_template('register.html', error=error)

        # Create a new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)  # Hash the password
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

    # Check if the old password is correct
    if not check_password_hash(current_user.password_hash, old_password):
        flash('Old password is incorrect.', 'danger')
        return redirect(url_for('profile'))

    # Check if new password matches confirm password
    if new_password != confirm_new_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('profile'))

    # Update password and save changes
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

    tours = Tour.query.all()  # Fetch all tours for admin view
    return render_template('admin_panel.html', tours=tours)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/edit_tour/<int:id>', methods=['GET', 'POST'])
def edit_tour(id):
    tour = Tour.query.get_or_404(id)
    if request.method == 'POST':
        # Update tour details based on form input
        tour.name = request.form.get('name')
        tour.description = request.form.get('description')
        tour.price_per_person = request.form.get('price_per_person')
        tour.available_spots = request.form.get('available_spots')
        # Handle image upload if necessary
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