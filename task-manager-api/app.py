from src.app import create_app
from src.config.settings import settings

app = create_app()


if __name__ == "__main__":
    app.run(debug=settings.DEBUG, host="0.0.0.0", port=settings.PORT)
