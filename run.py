from dotenv import load_dotenv

from app.web_app import create_app

load_dotenv()

# Порт и биндинг
PORT = 8000


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(PORT), reload=True)
