from src.app import create_app
from src.config.settings import settings

app = create_app()


if __name__ == "__main__":
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print(f"Rodando em http://localhost:{settings.PORT}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=settings.PORT)
