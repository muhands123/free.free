from flask import Flask, jsonify, send_from_directory
import os

app = Flask(__name__)

# روابط API الأساسية
@app.route("/api")
def home():
    return jsonify({"message": "مرحبًا! الخادم يعمل بنجاح 🚀"})

# لتقديم ملفات الواجهة الأمامية (React)
@app.route("/")
def serve_frontend():
    return send_from_directory("static", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

# لا تضع app.run() هنا!
