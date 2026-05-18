import os
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Movie, Comment, Rating

main = Blueprint('main', __name__)

GENRES = ['Боевик', 'Фантастика', 'Комедия', 'Драма', 'Фэнтези', 'Ужасы', 'Триллер', 'Приключения', 'Мелодрама', 'Детектив']

@main.route('/')
@main.route('/new')
def new():
    movies = Movie.query.filter_by(category='new').order_by(Movie.rating.desc()).all()
    return render_template('index.html', title='Новое', movies=movies, genres=GENRES, current_tab='new')

@main.route('/popular')
def popular():
    movies = Movie.query.filter_by(category='popular').order_by(Movie.rating.desc()).all()
    return render_template('index.html', title='Популярное', movies=movies, genres=GENRES, current_tab='popular')

@main.route('/films')
def films():
    movies = Movie.query.filter_by(category='film').order_by(Movie.rating.desc()).all()
    return render_template('index.html', title='Фильмы', movies=movies, genres=GENRES, current_tab='films')

@main.route('/series')
def series():
    movies = Movie.query.filter_by(category='series').order_by(Movie.rating.desc()).all()
    return render_template('index.html', title='Сериалы', movies=movies, genres=GENRES, current_tab='series')

@main.route('/favorites')
@login_required
def favorites():
    movies = current_user.favorite_movies.order_by(Movie.rating.desc()).all()
    return render_template('index.html', title='Избранное', movies=movies, genres=GENRES, current_tab='favorites')

@main.route('/genre/<genre_name>')
def by_genre(genre_name):
    movies = Movie.query.filter_by(genre=genre_name).order_by(Movie.rating.desc()).all()
    return render_template('index.html', title=f'Жанр: {genre_name}', movies=movies, genres=GENRES, current_tab=None)

@main.route('/search')
def search():
    query = request.args.get('query', '').strip()
    
    if not query:
        flash('Введите текст для поиска!', 'warning')
        return redirect(url_for('main.new'))
    
    all_movies = Movie.query.order_by(Movie.rating.desc()).all()
    movies = [m for m in all_movies if query.lower() in m.title.lower()]
    
    return render_template('index.html', 
                         title=f'Результаты поиска: "{query}"', 
                         movies=movies, 
                         genres=GENRES, 
                         current_tab=None,
                         search_query=query)

@main.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    
    similar_movies = Movie.query.filter(
        Movie.genre == movie.genre,
        Movie.id != movie.id
    ).order_by(Movie.rating.desc()).limit(6).all()
    
    user_rating = None
    if current_user.is_authenticated:
        user_rating = current_user.get_rating_for_movie(movie_id)
    
    return render_template('movie_detail.html', 
                         movie=movie, 
                         similar_movies=similar_movies, 
                         genres=GENRES,
                         user_rating=user_rating)

@main.route('/movie/<int:movie_id>/comment', methods=['POST'])
@login_required
def add_comment(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    text = request.form.get('comment', '').strip()
    
    if not text:
        flash('Комментарий не может быть пустым!', 'danger')
    elif len(text) > 500:
        flash('Комментарий не может быть длиннее 500 символов!', 'danger')
    else:
        comment = Comment(text=text, user_id=current_user.id, movie_id=movie_id)
        db.session.add(comment)
        db.session.commit()
        flash('Комментарий добавлен!', 'success')
    
    return redirect(url_for('main.movie_detail', movie_id=movie_id))

@main.route('/movie/<int:movie_id>/rate', methods=['POST'])
@login_required
def rate_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    score = request.form.get('score', type=int)
    
    if not score or score < 1 or score > 10:
        flash('Оценка должна быть от 1 до 10!', 'danger')
        return redirect(url_for('main.movie_detail', movie_id=movie_id))
    
    existing_rating = Rating.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    
    if existing_rating:
        existing_rating.score = score
    else:
        rating = Rating(score=score, user_id=current_user.id, movie_id=movie_id)
        db.session.add(rating)
    
    db.session.commit()
    movie.update_rating()
    
    flash(f'Ваша оценка {score}/10 сохранена!', 'success')
    return redirect(url_for('main.movie_detail', movie_id=movie_id))

@main.route('/toggle_favorite/<int:movie_id>', methods=['POST'])
@login_required
def toggle_favorite(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    
    if current_user.is_favorite(movie):
        current_user.remove_from_favorites(movie)
        db.session.commit()
        return jsonify({'status': 'removed', 'message': f'"{movie.title}" удалён из избранного'})
    else:
        current_user.add_to_favorites(movie)
        db.session.commit()
        return jsonify({'status': 'added', 'message': f'"{movie.title}" добавлен в избранное'})

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        age = request.form.get('age', '')
        gender = request.form.get('gender')
        favorite_genres = request.form.getlist('favorite_genres')
        avatar = request.files.get('avatar')
        
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Имя пользователя должно содержать минимум 3 символа!')
        
        if not password:
            errors.append('Пароль обязателен!')
        elif len(password) < 6:
            errors.append('Пароль должен содержать минимум 6 символов!')
        elif not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
            errors.append('Пароль должен содержать хотя бы одну букву и одну цифру!')
        
        if User.query.filter_by(username=username).first():
            errors.append('Пользователь с таким именем уже существует!')
        
        if age:
            try:
                age_int = int(age)
                if age_int < 1 or age_int > 120:
                    errors.append('Возраст должен быть от 1 до 120 лет!')
            except ValueError:
                errors.append('Возраст должен быть числом!')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', genres=GENRES)
        
        avatar_filename = 'default_avatar.png'
        if avatar and avatar.filename:
            avatar_filename = secure_filename(f"user_{username}_{avatar.filename}")
            avatar_path = os.path.join('app', 'static', 'uploads', avatar_filename)
            avatar.save(avatar_path)
        
        user = User(
            username=username,
            age=int(age) if age else None,
            gender=gender if gender else None,
            favorite_genres=','.join(favorite_genres) if favorite_genres else '',
            avatar=avatar_filename
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash(f'Добро пожаловать, {username}!', 'success')
        return redirect(url_for('main.new'))
    
    return render_template('register.html', genres=GENRES)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        
        if not username or not password:
            flash('Введите имя пользователя и пароль!', 'danger')
        elif user and user.check_password(password):
            login_user(user)
            flash(f'С возвращением, {username}!', 'success')
            return redirect(url_for('main.new'))
        else:
            flash('Неверное имя пользователя или пароль!', 'danger')
    
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта.', 'info')
    return redirect(url_for('main.new'))

@main.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'cover' not in request.files:
            return 'Файл не выбран', 400
        file = request.files['cover']
        if file.filename == '':
            return 'Файл не выбран', 400
        if file:
            filename = secure_filename(file.filename)
            upload_path = os.path.join('app', 'static', 'uploads', filename)
            file.save(upload_path)
            new_movie = Movie(title='Новый фильм', genre='Неизвестно', cover=filename, category='new')
            db.session.add(new_movie)
            db.session.commit()
            return f'Файл {filename} успешно загружен! <a href="/">На главную</a>'
    return render_template('upload.html')

@main.route('/api/movies')
def api_movies():
    movies = Movie.query.all()
    result = [{'id': m.id, 'title': m.title, 'genre': m.genre, 'cover': m.cover, 
               'description': m.description, 'category': m.category} for m in movies]
    return jsonify(result)