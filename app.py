"""A small Flask API — the thing we are going to containerize and ship.

Kept deliberately simple: the point of this project is the pipeline
around the code, not the code itself.
"""

import os

from flask import Flask, jsonify, request

app = Flask(__name__)

# Read at import time so `docker run -e APP_VERSION=...` actually changes
# the response. Config comes from the environment, never hardcoded.
APP_VERSION = os.environ.get("APP_VERSION", "0.1.0")


@app.get("/")
def index():
    return jsonify(
        service="flask-docker-ci",
        version=APP_VERSION,
        message="Hello from inside a container!",
    )


@app.get("/health")
def health():
    """Liveness probe. Docker, Kubernetes and load balancers poll this."""
    return jsonify(status="healthy", version=APP_VERSION)


@app.get("/api/greet/<name>")
def greet(name):
    return jsonify(greeting=f"Hello, {name}!")


@app.post("/api/sum")
def sum_numbers():
    """POST {"numbers": [1, 2, 3]} -> {"sum": 6}"""
    payload = request.get_json(silent=True) or {}
    numbers = payload.get("numbers")

    if not isinstance(numbers, list) or not numbers:
        return jsonify(error="send a non-empty JSON list under 'numbers'"), 400

    if not all(isinstance(n, int | float) and not isinstance(n, bool) for n in numbers):
        return jsonify(error="every item in 'numbers' must be a number"), 400

    return jsonify(sum=sum(numbers), count=len(numbers))


@app.errorhandler(404)
def not_found(_):
    return jsonify(error="not found"), 404


if __name__ == "__main__":
    # Development only. In the container, gunicorn runs the app instead.
    app.run(host="0.0.0.0", port=8000, debug=True)
