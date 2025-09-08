# recovery_agent/ui/app.py
from flask import Flask, jsonify


class StateManager:
    """A placeholder for a real state management object."""

    def get_status(self):
        # This is a mock implementation.
        return {
            "status": "idle",
            "last_run": None,
            "details": "No restoration has been run yet.",
        }


def create_app(state_manager=None):
    """Application factory to create and configure the Flask app."""
    app = Flask(__name__)

    if state_manager is None:
        state_manager = StateManager()

    @app.route("/healthz")
    def healthz():
        return "OK", 200

    @app.route("/status")
    def status():
        current_status = state_manager.get_status()
        return jsonify(current_status)

    return app