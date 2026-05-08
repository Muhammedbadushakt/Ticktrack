from flask import Blueprint,render_template

base_bp = Blueprint("base", __name__, url_prefix="")

@base_bp.route('/')
def index():
    return render_template('base.html')