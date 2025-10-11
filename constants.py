"""
Constants for the Trading Agent Bot

This module contains all constant values used across the application
to improve maintainability and avoid magic numbers.
"""

from typing import Final

# Telegram Message Limits
TELEGRAM_MAX_MESSAGE_LENGTH: Final[int] = 4096
TELEGRAM_MESSAGE_OVERHEAD: Final[int] = 600
MAX_ANALYSIS_LENGTH: Final[int] = TELEGRAM_MAX_MESSAGE_LENGTH - TELEGRAM_MESSAGE_OVERHEAD

# Analysis Timeouts and Delays
ANALYSIS_TIMEOUT_SECONDS: Final[int] = 300  # 5 minutes
LOADING_MESSAGE_UPDATE_INTERVAL: Final[int] = 10  # seconds

# Price Target Multipliers
PRICE_TARGET_BUY_MULTIPLIER: Final[float] = 1.10  # 10% above current
PRICE_TARGET_SELL_MULTIPLIER: Final[float] = 0.90  # 10% below current
PRICE_TARGET_HOLD_MULTIPLIER: Final[float] = 1.05  # 5% above current

# Confidence Levels
CONFIDENCE_HIGH: Final[int] = 8
CONFIDENCE_MEDIUM: Final[int] = 5
CONFIDENCE_LOW: Final[int] = 3

# Risk Keywords
RISK_HIGH_KEYWORDS: Final[set] = {'high', 'aggressive', 'volatile', 'risky'}
RISK_LOW_KEYWORDS: Final[set] = {'low', 'conservative', 'stable', 'safe'}

# Trading Recommendations
RECOMMENDATION_BUY: Final[str] = 'BUY'
RECOMMENDATION_SELL: Final[str] = 'SELL'
RECOMMENDATION_HOLD: Final[str] = 'HOLD'

# Risk Levels
RISK_LEVEL_HIGH: Final[str] = 'HIGH'
RISK_LEVEL_MEDIUM: Final[str] = 'MEDIUM'
RISK_LEVEL_LOW: Final[str] = 'LOW'

# Recommendation Emojis
RECOMMENDATION_EMOJIS: Final[dict] = {
    RECOMMENDATION_BUY: '🟢',
    RECOMMENDATION_SELL: '🔴',
    RECOMMENDATION_HOLD: '🟡',
}

# Message Emojis (using Unicode escapes for better compatibility)
EMOJI_SEARCH: Final[str] = '\U0001F50D'  # 🔍
EMOJI_ROBOT: Final[str] = '\U0001F916'  # 🤖
EMOJI_TIMER: Final[str] = '\U000023F1'  # ⏱️
EMOJI_CHART: Final[str] = '\U0001F4CA'  # 📊
EMOJI_ERROR: Final[str] = '\U0000274C'  # ❌
EMOJI_FILE: Final[str] = '\U0001F4C4'  # 📄
EMOJI_LIGHTNING: Final[str] = '\U000026A1'  # ⚡
EMOJI_CLOCK: Final[str] = '\U0001F550'  # 🕐
EMOJI_TARGET: Final[str] = '\U0001F3AF'  # 🎯
EMOJI_BRAIN: Final[str] = '\U0001F9E0'  # 🧠
EMOJI_BOOKS: Final[str] = '\U0001F4DA'  # 📚
EMOJI_WARNING: Final[str] = '\U000026A0'  # ⚠️
EMOJI_ROCKET: Final[str] = '\U0001F680'  # 🚀
EMOJI_CHART_UP: Final[str] = '\U0001F4C8'  # 📈

# File Settings
ANALYSIS_FILE_EXTENSION: Final[str] = '.txt'
DEFAULT_FILE_ENCODING: Final[str] = 'utf-8'

# Analysis Settings
DEFAULT_HISTORY_PERIOD: Final[str] = '2d'
MIN_CONFIDENCE_SCORE: Final[int] = 0
MAX_CONFIDENCE_SCORE: Final[int] = 10

# Report Formatting
REPORT_SEPARATOR: Final[str] = '=' * 80
REPORT_HEADER_SEPARATOR: Final[str] = '-' * 80

# TradingAgents Settings
TRADINGAGENTS_MAX_DEBATE_ROUNDS: Final[int] = 1
TRADINGAGENTS_DATA_VENDOR: Final[str] = 'yfinance'

# GLM API Settings
GLM_MODEL_VERSION: Final[str] = 'glm-4-32b-0414-128k'
GLM_API_BASE_URL: Final[str] = 'https://api.z.ai/api/paas/v4/'

# OpenAI Settings
OPENAI_EMBEDDING_MODEL: Final[str] = 'text-embedding-3-small'
OPENAI_API_BASE_URL: Final[str] = 'https://api.openai.com/v1'
