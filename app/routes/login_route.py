
from flask_jwt_extended import create_access_token
from flask import jsonify, request, Blueprint, render_template
from flask_jwt_extended import create_refresh_token, get_jwt_identity, verify_jwt_in_request
import json


login_bp = Blueprint('login', __name__)




# Маршрут для страницы входа
@login_bp.route('/login', methods=['GET'])
def login():
    return render_template('login.html')




# Выход из системы
@login_bp.route('/logout')
def logout():
    return jsonify({"msg": "Logout successful"}), 200



# Маршрут для входа (авторизации)
@login_bp.route('/auth', methods=['POST'])
def auth():
    from app.database.managers.user_manager import UserManager
    # Создаем экземпляр менеджера базы данных
    db = UserManager()
    login = request.json.get("login", None)
    password = request.json.get("password", None)

    # Проверяем пользователя в базе данных
    if not db.user_exists(login) or not db.check_password(login, password):
        return {"msg": "Bad username or password"}, 401
    # Генерируем Access и Refresh токены с дополнительной информацией
    access_token = create_access_token(identity=login)
    refresh_token = create_refresh_token(identity=login)

    return jsonify(access_token=access_token, refresh_token=refresh_token), 200


    

@login_bp.route('/refresh', methods=['POST'])
def refresh():
    # Получение токена из тела запроса
    refresh_token = request.json.get('refresh_token', None)
    if not refresh_token:
        return jsonify({"msg": "Missing refresh token"}), 400

    try:
        # Явная валидация токена
        verify_jwt_in_request(refresh=True, locations=["json"])
    except Exception as e:
        return jsonify({"msg": str(e)}), 401

    # Получение текущего пользователя
    current_user = get_jwt_identity()

    # Генерация нового access токена
    new_access_token = create_access_token(identity=current_user)
    new_refresh_token = create_refresh_token(identity = current_user)
    return jsonify(access_token= new_access_token, refresh_token= new_refresh_token), 200