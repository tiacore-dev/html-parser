from flask import Blueprint, request, jsonify
from flask import render_template
from flask_jwt_extended import jwt_required
from app.decorators import api_key_required


logs_bp = Blueprint('logs', __name__)


@logs_bp.route('/logs')
def logs_page():
    return render_template('logs.html')


@logs_bp.route('/client/logs', methods=['GET'])
@jwt_required()
def get_logs():
    date = request.args.get('date')
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 10))
    from app.database.managers.logs_manager import LogManager
    log_manager = LogManager()
    logs, total_count = log_manager.get_logs_paginated(
        date=date, offset=offset, limit=limit)
    # Убедитесь, что возвращаете правильный формат
    return jsonify({'total': total_count, 'logs': logs})


@logs_bp.route('/api/logs', methods=['GET'])
@api_key_required
def get_logs_api():
    date = request.args.get('date')

    from app.database.managers.logs_manager import LogManager
    log_manager = LogManager()
    logs = log_manager.get_logs(date=date)
    # Убедитесь, что возвращаете правильный формат
    return jsonify({'logs': logs})
