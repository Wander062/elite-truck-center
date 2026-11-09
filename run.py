import os

from app import create_app

app = create_app(os.environ.get("APP_ENV", "development"))

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", "5000"))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(host=host, port=porta, debug=debug)
