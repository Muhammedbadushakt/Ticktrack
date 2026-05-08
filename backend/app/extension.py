from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from pwdlib import PasswordHash
from openai import OpenAI
from app.config import Config

db= SQLAlchemy()
mail = Mail()
p = PasswordHash.recommended()
client = OpenAI(
    base_url=Config.OPENROUTER_BASE_URL,
    api_key=Config.OPENROUTER_API_KEY,
)