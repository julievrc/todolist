from flask import Flask, render_template, request, redirect, jsonify, url_for
import requests
import os

app = Flask(__name__)
API_URL = os.environ.get('API_URL', 'http://localhost:5050')

@app.route("/")
def show_list():
    return render_template("index.html")

@app.route("/test")
def test_page():
    return render_template("test.html")

@app.route("/health")
def health_check():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run("0.0.0.0", port=80)
