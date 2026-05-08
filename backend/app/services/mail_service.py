from flask_mail import Message
from app.extension import mail
from flask import current_app
import os

def send_otp_email(to_email: str, otp: str):
    msg = Message(
        subject="Your OTP For Password Reset",
        sender= current_app.config.get("MAIL_USERNAME"),
        recipients=[to_email],
        body=f"""
Hi there!

Your OTP for Password Reset is:

    {otp}

This OTP is valid for 10 minutes. Do not share it with anyone.

- C.S.A DEPARTMENT COCHIN UNIVERSITY OF SCIENCE AND TECHNOLOGY
        """
    )
    mail.send(msg)