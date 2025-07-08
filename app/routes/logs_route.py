from flask import Blueprint, jsonify, render_template, request
from flask_jwt_extended import jwt_required

from app.decorators import api_key_required

logs_bp = Blueprint("logs", __name__)


@logs_bp.route("/logs/", methods=["GET"])
def logs_page():
    """Рендеринг страницы логов"""
    return render_template("logs.html")


@logs_bp.route("/logs/api", methods=["GET"])
@jwt_required()
def get_logs():
    """API для получения логов с фильтрацией"""
    date = request.args.get("date")
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 10))
    search = request.args.get("search", None)
    keywords = request.args.get("keywords", None)  # Получаем ключевые слова

    from app.database.managers.logs_manager import LogManager

    log_manager = LogManager()

    # Разбиваем ключевые слова на массив (если они есть)
    keyword_list = [kw.strip() for kw in keywords.split(",")] if keywords else []

    logs, total_count = log_manager.get_logs_paginated(date=date, search=search, keywords=keyword_list, offset=offset, limit=limit)

    return jsonify({"total": total_count, "logs": logs})


@logs_bp.route("/api/logs", methods=["GET"])
@api_key_required
def get_logs_api():
    date = request.args.get("date")

    from app.database.managers.logs_manager import LogManager

    log_manager = LogManager()
    logs = log_manager.get_logs(date=date)
    # Убедитесь, что возвращаете правильный формат
    return jsonify({"logs": logs})
