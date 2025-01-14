# from app.parsers.post_master_parse import post_master
# from app.parsers.plex_post_parse import plex_post, extract_delivered_info
from app.parsers.vip_mail_ufa_parse import vip_mail_ufa
from app.parsers.svs import get_orders


def test_vip_mail():
    orders = get_orders("90b470a2-a775-11e7-ad08-74d43522d93b")
    for order in orders:
        order_number = order.get('number')
        info = vip_mail_ufa(order_number)
        print(info)
        # if info:
        # print()
