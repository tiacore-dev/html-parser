from flask import Blueprint, jsonify, request
import logging
from decorators import api_key_required
import json
from parsers.courierexe_parse import courierexe
# Получаем логгер по его имени
logger = logging.getLogger('parser')

gateway_bp = Blueprint('gateway', __name__)

@gateway_bp.route('/api/courierexe', methods=['POST'])
@api_key_required
def courierexe():
    data = request.json
    orderno=data.get('orderno')
    info = courierexe(orderno)
    return jsonify(info)