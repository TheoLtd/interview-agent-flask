from flask import Blueprint

practice_bp = Blueprint('practice', __name__, url_prefix='/practice')

from . import routes