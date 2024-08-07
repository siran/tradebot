import os

ALPACA_ENDPOINT = "https://api.alpaca.markets"
ALPACA_KEYID = "modify"
ALPACA_SECRETKEY = "xxxxx"

os.environ["APCA_API_KEY_ID"] = ALPACA_KEYID
os.environ["APCA_API_SECRET_KEY"] = ALPACA_SECRETKEY
os.environ["APCA_API_BASE_URL"] = ALPACA_ENDPOINT
