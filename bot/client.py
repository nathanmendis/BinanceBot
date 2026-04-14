import os
from binance.client import Client
from binance.enums import *
from dotenv import load_dotenv
from .logging_config import logger

load_dotenv()

class BinanceClient:
    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            logger.error("API Key or Secret missing in environment variables.")
            raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET must be set.")
            
        try:
            # We use testnet=True for Futures Testnet
            self.client = Client(self.api_key, self.api_secret, testnet=True)
            logger.info("Binance Client initialized on Testnet.")
        except Exception as e:
            logger.error(f"Failed to initialize Binance Client: {e}")
            raise

    def get_futures_client(self):
        return self.client
