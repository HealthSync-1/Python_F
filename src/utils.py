# src/utils.py
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

def get_credentials():
    user_ = os.getenv("USER")
    pass_ = os.getenv("PASSWORD")
    if not user_:
        user_ = input("Digite seu usuário Oracle: ")
    if not pass_:
        pass_ = input("Digite sua senha Oracle: ")
    return user_, pass_

# Helpers de data
FMT_DATE = "%d/%m/%Y"
FMT_DATETIME = "%d/%m/%Y %H:%M"

def parse_date_br(s: str):
    return datetime.strptime(s.strip(), FMT_DATE)

def parse_datetime_br(s: str):
    return datetime.strptime(s.strip(), FMT_DATETIME)

def yn_to_char(v: bool) -> str:
    return "S" if v else "N"

def char_to_bool(c: str) -> bool:
    return (c or "N").upper() == "S"
