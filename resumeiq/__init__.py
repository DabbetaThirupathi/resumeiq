"""ResumeIQ - AI-powered resume screening and ATS score analyzer."""

from flask import Flask

__version__ = "1.0.0"


def create_app(config=None):
    """Application factory."""
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.update(
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5 MB per request
        JSON_SORT_KEYS=False,
    )
    if config:
        app.config.update(config)

    from .routes import bp
    app.register_blueprint(bp)
    return app
