from flask import Flask

from .account_route import account_bp
from .info_route import info_bp
from .login_route import login_bp
from .logs_route import logs_bp


def register_routes(app: Flask):
    app.register_blueprint(login_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(info_bp)
