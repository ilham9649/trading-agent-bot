"""Configuration management for the Trading Agent Bot.

This module handles all configuration settings including:
- Environment variable loading and validation
- API key management
- Bot behavior settings
- Trading parameters
"""

import os
import logging
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when there's a configuration error."""
    pass


class Config:
    """Configuration class for the trading bot.
    
    This class manages all configuration settings loaded from environment
    variables. It provides validation and sensible defaults.
    
    Attributes:
        TELEGRAM_BOT_TOKEN: Bot token from Telegram BotFather
        OPENAI_API_KEY: OpenAI API key for embeddings
        GLM_API_KEY: Z.AI (GLM) API key for analysis
        FINNHUB_API_KEY: Finnhub API key for market data
        ALPHA_VANTAGE_API_KEY: Alpha Vantage API key for news data
        BOT_DEBUG: Enable debug mode
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        DEFAULT_TIMEFRAME: Default timeframe for stock data
        MAX_RECOMMENDATIONS: Maximum number of recommendations to return
    """
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    GLM_API_KEY: Optional[str] = os.getenv('GLM_API_KEY')
    FINNHUB_API_KEY: Optional[str] = os.getenv('FINNHUB_API_KEY')
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    # Bot Settings
    BOT_DEBUG: bool = os.getenv('BOT_DEBUG', 'False').lower() in ('true', '1', 'yes')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Trading Settings
    DEFAULT_TIMEFRAME: str = os.getenv('DEFAULT_TIMEFRAME', '1d')
    MAX_RECOMMENDATIONS: int = int(os.getenv('MAX_RECOMMENDATIONS', '5'))
    
    # File Settings
    RESULTS_DIR: Path = Path(os.getenv('RESULTS_DIR', './eval_results'))
    LOG_FILE: Path = Path(os.getenv('LOG_FILE', './bot.log'))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present and valid.
        
        Returns:
            bool: True if all validation passes
            
        Raises:
            ConfigurationError: If required variables are missing or invalid
        """
        errors: List[str] = []
        
        # Check required variables
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'GLM_API_KEY',
            'FINNHUB_API_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            errors.append(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
        
        # Validate LOG_LEVEL
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if cls.LOG_LEVEL not in valid_log_levels:
            errors.append(
                f"Invalid LOG_LEVEL '{cls.LOG_LEVEL}'. "
                f"Must be one of: {', '.join(valid_log_levels)}"
            )
        
        # Validate numeric settings
        if cls.MAX_RECOMMENDATIONS < 1:
            errors.append("MAX_RECOMMENDATIONS must be at least 1")
        
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(
                f"  - {error}" for error in errors
            )
            raise ConfigurationError(error_message)
        
        logger.info("Configuration validated successfully")
        return True
    
    @classmethod
    def get_summary(cls) -> str:
        """Get a summary of current configuration (safe for logging).
        
        Returns:
            str: Configuration summary with sensitive data masked
        """
        def mask_key(key: Optional[str]) -> str:
            """Mask API key for safe logging."""
            if not key:
                return "Not set"
            if len(key) < 8:
                return "***"
            return f"{key[:4]}...{key[-4:]}"
        
        return f"""
Configuration Summary:
  Telegram Token: {mask_key(cls.TELEGRAM_BOT_TOKEN)}
  OpenAI API Key: {mask_key(cls.OPENAI_API_KEY)}
  GLM API Key: {mask_key(cls.GLM_API_KEY)}
  Finnhub API Key: {mask_key(cls.FINNHUB_API_KEY)}
  Alpha Vantage API Key: {mask_key(cls.ALPHA_VANTAGE_API_KEY)}
  Debug Mode: {cls.BOT_DEBUG}
  Log Level: {cls.LOG_LEVEL}
  Default Timeframe: {cls.DEFAULT_TIMEFRAME}
  Max Recommendations: {cls.MAX_RECOMMENDATIONS}
"""