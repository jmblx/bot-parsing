import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

ADMIN_LIST = (os.getenv("ADMIN_LIST", "1039610272")).split(",")

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")

DB_URL = os.environ.get("DB_URL")

REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = os.environ.get("REDIS_PORT")
