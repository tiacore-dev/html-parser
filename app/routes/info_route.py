import logging
from flask import Blueprint, jsonify, request
from app.decorators import api_key_required
from app.parsers.sp_service_tyumen_parse import sp_service_tyumen  # pylint: disable=unused-import
from app.parsers.sp_service_ekaterinburg_parse import sp_service_ekaterinburg  # pylint: disable=unused-import
from app.parsers.rasstoyaniya_net_parse import rasstoyaniya_net  # pylint: disable=unused-import
from app.parsers.sib_express_parse import sib_express  # pylint: disable=unused-import
from app.parsers.post_master_parse import post_master  # pylint: disable=unused-import
from app.parsers.plex_post_parse import plex_post  # pylint: disable=unused-import

# Получаем логгер по его имени
logger = logging.getLogger('parser')

info_bp = Blueprint('info', __name__)


@info_bp.route('/api/info', methods=['POST'])
@api_key_required
def get_info():
    orderno = request.json.get("order_number", None)
    client = request.json.get("client", None)
    if not (orderno and client):
        return jsonify({"msg": "No data given"}), 400
    function = globals().get(client)
    try:
        info = function(orderno)
        return jsonify({"msg": "Data fetched successfully", "info": info}), 200
    except Exception as e:
        return jsonify({"msg": f"Error during fetching data: {e}"}), 500
