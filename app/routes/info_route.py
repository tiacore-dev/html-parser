import logging

from flask import Blueprint, jsonify, request

from app.decorators import api_key_required
from app.parsers.plex_post_parser import PlexPostParser
from app.parsers.post_master_parser import PostMasterParser
from app.parsers.rasstoyaniya_net_parser import RasstoyaniyaNetParser
from app.parsers.sib_express_parser import SibExpressParser
from app.parsers.sp_service_ekaterinburg_parser import SPServiceEkaterinburgParser
from app.parsers.sp_service_tyumen_parser import SPServiceTyumenParser
from app.parsers.vip_mail_ufa_parser import VIPMailUfaParser

partners_old = {
    "sp_service_tyumen": "26d49356-559c-11eb-80ef-74d43522d93b",
    "sp_service_ekaterinburg": "1d4be527-c61e-11e7-9bdb-74d43522d93b",
    "sib_express": "33c8793d-96c2-11e7-b541-00252274a609",
    "rasstoyaniya_net": "b3116f3b-9f4a-11e7-a536-00252274a609",
    "post_master": "1034e0be-855a-11ea-80dd-74d43522d93b",
    "plex_post": "d56a2a0c-6339-11e8-80b5-74d43522d93b",
    "vip_mail_ufa": "90b470a2-a775-11e7-ad08-74d43522d93b",
}

partners = {
    "26d49356-559c-11eb-80ef-74d43522d93b": SPServiceTyumenParser(),
    "1d4be527-c61e-11e7-9bdb-74d43522d93b": SPServiceEkaterinburgParser(),
    "33c8793d-96c2-11e7-b541-00252274a609": SibExpressParser(),
    "b3116f3b-9f4a-11e7-a536-00252274a609": RasstoyaniyaNetParser(),
    "1034e0be-855a-11ea-80dd-74d43522d93b": PostMasterParser(),
    "d56a2a0c-6339-11e8-80b5-74d43522d93b": PlexPostParser(),
    "90b470a2-a775-11e7-ad08-74d43522d93b": VIPMailUfaParser(),
}

# Получаем логгер по его имени
logger = logging.getLogger("parser")

info_bp = Blueprint("info", __name__)


@info_bp.route("/api/info", methods=["POST"])
@api_key_required
def get_info():
    if not request.json:
        return jsonify({"msg": "Bad request"}), 400
    orderno = request.json.get("order_number", None)
    client = request.json.get("client", None)

    logger.info("Received request for fetching info.")

    if not (orderno and client):
        logger.warning("Request missing required fields: order_number or client.")
        return jsonify({"msg": "No data given"}), 400

    logger.info(
        f"""Processing request with order_number: {orderno}, client: {client}"""
    )

    for partner_id, parser in partners.items():
        if client == partner_id:
            logger.debug(
                f"""Found matching client: {client} with partner key: {parser.name}"""
            )

            try:
                info = parser.parse(orderno)
                logger.info(f"Data fetched successfully for order_number: {orderno}")
                return jsonify({"msg": "Data fetched successfully", "info": info}), 200
            except Exception as e:
                logger.exception(
                    f"""Error during fetching data for order_number: {
                        orderno
                    } and client: {client}"""
                )
                return jsonify({"msg": f"Error during fetching data: {e}"}), 500

    logger.warning(f"No matching partner found for client: {client}")
    return jsonify({"msg": "Client not found"}), 404
