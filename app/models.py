from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    avatar = db.Column(db.String(300), default='default_avatar.png')
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    favorite_genres = db.Column(db.String(300))
    
    favorite_movies = db.relationship('Movie', secondary=favorites, 
                                      lazy='dynamic', 
                                      backref=db.backref('favorited_by', lazy='dynamic'))
    
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    ratings = db.relationship('Rating', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_favorite_genres_list(self):
        if self.favorite_genres:
            return self.favorite_genres.split(',')
        return []
    
    def is_favorite(self, movie):
        return self.favorite_movies.filter(favorites.c.movie_id == movie.id).count() > 0
    
    def add_to_favorites(self, movie):
        if not self.is_favorite(movie):
            self.favorite_movies.append(movie)
    
    def remove_from_favorites(self, movie):
        if self.is_favorite(movie):
            self.favorite_movies.remove(movie)
    
    def get_rating_for_movie(self, movie_id):
        rating = Rating.query.filter_by(user_id=self.id, movie_id=movie_id).first()
        return rating.score if rating else None

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    cover = db.Column(db.String(300), default='default_cover.jpg')
    description = db.Column(db.Text, default='')
    category = db.Column(db.String(50))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float, default=0.0)
    folder_id = db.Column(db.String(200))
    trailer_id = db.Column(db.String(200))
    
    comments = db.relationship('Comment', backref='movie', lazy='dynamic', 
                               order_by='Comment.created_at.desc()')
    ratings = db.relationship('Rating', backref='movie', lazy='dynamic')
    
    def update_rating(self):
        ratings = Rating.query.filter_by(movie_id=self.id).all()
        if ratings:
            self.rating = round(sum(r.score for r in ratings) / len(ratings), 1)
        else:
            self.rating = 0.0
        db.session.commit()

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'movie_id', name='unique_user_movie_rating'),)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def seed_data():
    if Movie.query.first() is None:
        sample_movies = [
            Movie(title='Интерстеллар', genre='Фантастика', category='new', year=2014, rating=0.0,
                  description='Путешествие через червоточину для спасения человечества.',
                  folder_id='15e2co6nZZshjfj7ayxYk3jCnGUm5dnsv',
                  trailer_id='1y2IH3MMQjVNdvJF84OQdKQ7sDe9Qf2w5',
                  cover='interstellar_2014.jpg'),
            Movie(title='1+1', genre='Комедия', category='new', year=2011, rating=0.0,
                  description='Аристократ нанимает сиделку из бедного района.',
                  cover='1+1_2011.jpg'),
            Movie(title='Начало', genre='Фантастика', category='new', year=2010, rating=0.0,
                  description='Внедрение идей через сны.',
                  cover='inception_2010.jpg'),
            Movie(title='Побег из Шоушенка', genre='Драма', category='new', year=1994, rating=0.0,
                  description='Несправедливо осуждённый банкир планирует побег.',
                  cover='shawshank_1994.jpg'),
            Movie(title='Форрест Гамп', genre='Драма', category='new', year=1994, rating=0.0,
                  description='История человека, изменившего мир, сам того не желая.',
                  cover='forrest_gump_1994.jpg'),
            Movie(title='Одержимость', genre='Драма', category='new', year=2014, rating=0.0,
                  description='Молодой барабанщик и его жестокий наставник.',
                  cover='whiplash_2014.jpg'),
            Movie(title='Бегущий по лезвию 2049', genre='Фантастика', category='new', year=2017, rating=0.0,
                  description='Продолжение культовой антиутопии.',
                  cover='blade_runner_2049_2017.jpg'),
            
            Movie(title='Джон Уик', genre='Боевик', category='popular', year=2014, rating=0.0,
                  description='Киллер мстит за смерть щенка.',
                  cover='john_wick_2014.jpg'),
            Movie(title='Тёмный рыцарь', genre='Боевик', category='popular', year=2008, rating=0.0,
                  description='Бэтмен против Джокера в Готэме.',
                  cover='dark_knight_2008.jpg'),
            Movie(title='Криминальное чтиво', genre='Драма', category='popular', year=1994, rating=0.0,
                  description='Несколько переплетённых историй из криминального мира.',
                  cover='pulp_fiction_1994.jpg'),
            Movie(title='Гладиатор', genre='Драма', category='popular', year=2000, rating=0.0,
                  description='Римский генерал становится гладиатором.',
                  cover='gladiator_2000.jpg'),
            Movie(title='Достать ножи', genre='Детектив', category='popular', year=2019, rating=0.0,
                  description='Детектив расследует смерть писателя.',
                  cover='knives_out_2019.jpg'),
            Movie(title='Дюна', genre='Фантастика', category='popular', year=2021, rating=0.0,
                  description='Борьба за пряность на пустынной планете.',
                  cover='dune_2021.jpg'),
            Movie(title='Мстители: Финал', genre='Фантастика', category='popular', year=2019, rating=0.0,
                  description='Финальная битва с Таносом.',
                  cover='avengers_endgame_2019.jpg'),
            
            Movie(title='Матрица', genre='Фантастика', category='film', year=1999, rating=0.0,
                  description='Выбери красную таблетку.',
                  cover='matrix_1999.jpg'),
            Movie(title='Бойцовский клуб', genre='Драма', category='film', year=1999, rating=0.0,
                  description='Первое правило бойцовского клуба.',
                  cover='fight_club_1999.jpg'),
            Movie(title='Остров проклятых', genre='Триллер', category='film', year=2010, rating=0.0,
                  description='Маршалы расследуют исчезновение пациентки.',
                  cover='shutter_island_2010.jpg'),
            Movie(title='Зелёная книга', genre='Комедия', category='film', year=2018, rating=0.0,
                  description='Путешествие пианиста и водителя по югу США.',
                  cover='green_book_2018.jpg'),
            Movie(title='Сияние', genre='Ужасы', category='film', year=1980, rating=0.0,
                  description='Писатель сходит с ума в пустом отеле.',
                  cover='shining_1980.jpg'),
            Movie(title='Леон', genre='Драма', category='film', year=1994, rating=0.0,
                  description='Киллер защищает 12-летнюю девочку.',
                  cover='leon_1994.jpg'),
            Movie(title='Назад в будущее', genre='Приключения', category='film', year=1985, rating=0.0,
                  description='Путешествие во времени на DeLorean.',
                  cover='back_to_future_1985.jpg'),
            
            Movie(title='Во все тяжкие', genre='Драма', category='series', year=2008, rating=0.0,
                  description='Учитель химии становится наркобароном.',
                  cover='breaking_bad_2008.jpg'),
            Movie(title='Игра престолов', genre='Фэнтези', category='series', year=2011, rating=0.0,
                  description='Битва за Железный трон.',
                  cover='game_of_thrones_2011.jpg'),
            Movie(title='Шерлок', genre='Детектив', category='series', year=2010, rating=0.0,
                  description='Современный Шерлок Холмс в Лондоне.',
                  cover='sherlock_2010.jpg'),
            Movie(title='Настоящий детектив', genre='Детектив', category='series', year=2014, rating=0.0,
                  description='Два детектива расследуют ритуальное убийство.',
                  cover='true_detective_2014.jpg'),
            Movie(title='Очень странные дела', genre='Фантастика', category='series', year=2016, rating=0.0,
                  description='Дети сталкиваются с параллельным измерением.',
                  cover='stranger_things_2016.jpg'),
            Movie(title='Чернобыль', genre='Драма', category='series', year=2019, rating=0.0,
                  description='Катастрофа на ЧАЭС и её последствия.',
                  cover='chernobyl_2019.jpg'),
            Movie(title='Рик и Морти', genre='Комедия', category='series', year=2013, rating=0.0,
                  description='Приключения учёного и внука в мультивселенной.',
                  cover='rick_and_morty_2013.jpg'),
            Movie(title='Офис', genre='Комедия', category='series', year=2005, rating=0.0,
                  description='Будни провинциального офиса.',
                  cover='office_2005.jpg'),
        ]
        db.session.add_all(sample_movies)
        db.session.commit()