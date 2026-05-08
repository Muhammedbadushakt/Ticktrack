import os 
from dotenv import load_dotenv
load_dotenv()
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is not set!")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL is not set!")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "storage",
        "static",
        "uploads"
    )
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    MAIL_SERVER          = "smtp.gmail.com"
    MAIL_PORT            = 587
    MAIL_USE_TLS         = True
    MAIL_USE_SSL         = False        # ← explicitly set False
    MAIL_USERNAME        = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD        = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER  = os.getenv("MAIL_USERNAME")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"