import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

#Bot token @Botfather
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

#Your API ID from my.telegram.org
API_ID = int(os.environ.get("API_ID", ""))

#Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "")

# OWNER IDs
OWNER_ID = list({1008848605} | set(map(int, os.environ.get("OWNER_ID", "").split(","))) if os.environ.get("OWNER_ID") else {1008848605})

#Database 
DB_URI = os.environ.get("DB_URI", "")

#Your Logs Channel/Group ID
LOGS_CHAT_ID = int(os.environ.get("LOGS_CHAT_ID", ""))

#Your Dump Channel/Group ID
DUMP_CHAT_ID = int(os.environ.get("DUMP_CHAT_ID", ""))

#Your Start Image Url
Start_IMG = os.environ.get("Start_IMG", "")

#Force Sub Channel ID
FSUB_ID = int(os.environ.get("FSUB_ID", "") or 0) or None

#Force Sub Channel Invite Link
FSUB_INV_LINK = os.environ.get("FSUB_INV_LINK", "")

# Shortner Api Url For Token
TOKEN_API_URL = os.environ.get("TOKEN_API_KEY", "https://arolinks.com/api")

#Api Key For Token
TOKEN_API_KEY = os.environ.get("TOKEN_API_KEY", "e425c537944dc2fe1fe0b824e2fb5748ba1be914")
