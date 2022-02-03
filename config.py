import os

from dotenv import load_dotenv


load_dotenv()

API_SERVER_URL = os.getenv('API_SERVER_URL')
TG_API_TOKEN = os.getenv('TG_API_TOKEN')
IMGBB_TOKEN = os.getenv('IMGBB_TOKEN')