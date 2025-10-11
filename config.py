import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the trading bot"""
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GLM_API_KEY = os.getenv('GLM_API_KEY')
    FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
    
    # Bot Settings
    BOT_DEBUG = os.getenv('BOT_DEBUG', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Trading Settings
    DEFAULT_TIMEFRAME = '1d'
    MAX_RECOMMENDATIONS = 5
    
    # Validation
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'GLM_API_KEY', 
            'FINNHUB_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True