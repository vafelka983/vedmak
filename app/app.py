import json
import os
import csv
import io
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify, Response, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

REVIEWS_FILE = 'reviews.json'

def school_required(required_school):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('school') != required_school:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def load_reviews():
    if not os.path.exists(REVIEWS_FILE):
        return []
    with open(REVIEWS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_reviews(reviews):
    with open(REVIEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=4)

alchemy_items = [
    {"name": "Черная кровь", "type": "potion", "toxicity": 10},
    {"name": "Золотая иволга", "type": "potion", "toxicity": 15},
    {"name": "Разрывной болт", "type": "bomb", "toxicity": 5},
    {"name": "Ирден", "type": "bomb", "toxicity": 8},
]

@app.route('/alchemy')
def alchemy():
    item_type = request.args.get('type')
    toxicity = request.args.get('toxicity', type=int)

    if not item_type or toxicity is None:
        return jsonify({"error": "Параметры 'type' и 'toxicity' обязательны"}), 400

    filtered_items = [
        item["name"] for item in alchemy_items
        if item["type"] == item_type and item["toxicity"] <= toxicity
    ]

    json_str = json.dumps(filtered_items, ensure_ascii=False)
    return Response(json_str, mimetype='application/json')

@app.route('/reviews', methods=['GET', 'POST'])
@login_required
def reviews():
    reviews = load_reviews()

    if request.method == 'POST':
        contract_name = request.form.get('contract_name', '').strip()
        rating = request.form.get('rating', '').strip()
        comment = request.form.get('comment', '').strip()

        if not contract_name:
            flash('Пожалуйста, укажите название контракта.')
            return redirect(url_for('reviews'))
        if rating not in ['1', '2', '3', '4', '5']:
            flash('Пожалуйста, выберите корректную оценку от 1 до 5.')
            return redirect(url_for('reviews'))

        reviews.append({
            "contract_name": contract_name,
            "rating": int(rating),
            "comment": comment
        })
        save_reviews(reviews)
        flash('Спасибо за ваш отзыв!')
        return redirect(url_for('reviews'))

    return render_template('reviews.html', reviews=reviews)

users_db = {
    "Geralt": {
        "id": "1",
        "username": "Геральт из Ривии",
        "password": "witcher123",
        "school": "Волка",
        "rank": "Мастер",
        "signs": ["Игни", "Аард", "Квен", "Аксий", "Ирден"],
        "stats": {
            "Жизненная сила": "3500",
            "Токсичность": "80",
            "Опыт": "12000",
            "Уровень": "22"
        }
    }
}


class User(UserMixin):
    def __init__(self, id, username, school, rank, signs=None, stats=None):
        self.id = id
        self.username = username
        self.school = school
        self.rank = rank
        self.signs = signs or []
        self.stats = stats or {}


@login_manager.user_loader
def load_user(user_id):
    for user_data in users_db.values():
        if user_data["id"] == user_id:
            return User(
                user_data["id"],
                user_data["username"],
                user_data["school"],
                user_data["rank"],
                user_data.get("signs"),
                user_data.get("stats")
            )
    return None

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        school = request.form.get('school')

        user_data = users_db.get(username)
        if user_data and user_data["password"] == password and user_data["school"] == school:
            user = User(
                user_data["id"],
                user_data["username"],
                user_data["school"],
                user_data["rank"],
                user_data.get("signs"),
                user_data.get("stats")
            )
            login_user(user)
            session['school'] = school
            return redirect(url_for('profile'))
        else:
            error = "Неверные данные или школа"
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/profile')
@login_required
def profile():
    return render_template(
        'profile.html',
        witcher={
            "name": current_user.username,
            "school": current_user.school,
            "signs": current_user.signs,
            "stats": current_user.stats
        },
        rank=current_user.rank
    )

@app.route('/contracts')
@login_required
def contracts():
    if current_user.rank != "Мастер":
        abort(403)
    contracts_list = [
        {"monster": "Вурдалак", "reward": 150, "date": "2025-05-01"},
        {"monster": "Дракон", "reward": 1000, "date": "2025-04-25"},
        {"monster": "Гуль", "reward": 200, "date": "2025-05-10"},
    ]
    total = sum(contract.get('reward', 0) for contract in contracts_list)
    return render_template('contracts.html', contracts=contracts_list, total_gold=total)

def total_gold(contracts_list):
    return sum(contract.get('reward', 0) for contract in contracts_list)

@app.route('/contracts/report')
@login_required
def contracts_report():
    if current_user.rank != "Мастер":
        abort(403)

    contracts_list = [
        {"monster": "Вурдалак", "reward": 150, "date": "2025-05-01"},
        {"monster": "Дракон", "reward": 1000, "date": "2025-04-25"},
        {"monster": "Гуль", "reward": 200, "date": "2025-05-10"},
    ]

    si = io.StringIO()
    si.write('\ufeff')
    cw = csv.writer(si, delimiter=';')
    cw.writerow(["Название монстра", "Вознаграждение (золото)", "Дата выполнения"])
    for c in contracts_list:
        cw.writerow([c["monster"], c["reward"], c["date"]])

    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=contracts_report.csv"}
    )


@app.errorhandler(403)
def forbidden(e):
    return "<h1>403 Доступ запрещён</h1><p>У вас нет прав для просмотра этой страницы.</p>", 403

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))

@app.route('/kaermorhen')
@login_required
@school_required('Волка')
def kaermorhen():
    return render_template('kaermorhen.html')

@app.route('/witcher/stats')
@login_required
def witcher_stats():
    witcher = {
        "name": current_user.username,
        "school": current_user.school,
        "rank": current_user.rank,
        "equipment": session.get('equipment', ["Нет снаряжения"]),
        "toxicity": current_user.stats.get("Токсичность", "Неизвестно"),
        "active_quests": session.get('active_quests', [])
    }

    return render_template('witcher_stats.html', witcher=witcher)


if __name__ == '__main__':
    app.run(debug=True)
