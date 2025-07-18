import os

from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()
api_key = os.getenv("API_KEY")


async def check_api_key(x_api_key: str = Header(...)):
    if str(x_api_key) == str(api_key):
        return "ok"
    else:
        raise HTTPException(status_code=401, detail="Неверный апи ключ")
