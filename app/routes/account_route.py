from flask import Blueprint, jsonify, request, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import json
# Получаем логгер по его имени
logger = logging.getLogger('parser')

account_bp = Blueprint('account', __name__)

@account_bp.route('/account', methods=['GET'])
def account():
    return render_template('account.html')

@account_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    try:
        current_user = get_jwt_identity()
        current_user=json.loads(current_user)
        logger.info(f"Пользователь авторизован: {current_user}")
        return jsonify({"message": "Access granted"}), 200
    except Exception as e:
        logger.error(f"Ошибка авторизации: {str(e)}")
        return jsonify({"error": "Authorization failed"}), 401


@account_bp.route('/get_username', methods=['GET'])
@jwt_required()  # Требуется авторизация с JWT
def get_username():
    current_user = get_jwt_identity()
    current_user=json.loads(current_user)
    from app.database.managers.user_manager import UserManager
    # Создаем экземпляр менеджера базы данных
    db = UserManager()
    logger.info(f"Запрос имени пользователя от пользователя: {current_user['user_id']}")
    user=db.get_user_by_user_id(current_user['user_id'])
    username=user.username
    logger.info(f"Получено имя пользователя: {username}")
    return jsonify(username), 200