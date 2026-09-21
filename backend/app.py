# 纯 JSON API：只挂 /api 蓝图，不再托管任何 HTML（前端是独立的 Vue 应用 frontend/）。
from flask import Flask
from flask_cors import CORS

from backend.oil import oil_bp
from backend.bank import bank_bp
from backend.industry import industry_bp
from backend.holders import holders_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(oil_bp, url_prefix="/api")
app.register_blueprint(bank_bp, url_prefix="/api")
app.register_blueprint(industry_bp, url_prefix="/api")
app.register_blueprint(holders_bp, url_prefix="/api")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
