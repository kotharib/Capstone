"""
Configuration management for Baseline Agent
Loads settings from .env file
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
PROJECT_ROOT = Path(__file__).parent
ENV_FILE = PROJECT_ROOT / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    raise FileNotFoundError(f".env file not found at {ENV_FILE}")


class Config:
    """Configuration container for the agent"""

    # Application settings
    APP_NAME = os.getenv("APP_NAME", "Baseline Banking AI Agent")
    APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Logging settings
    LOG_FILE = os.getenv("LOG_FILE", "agent_baseline.log")

    # Agent behavior
    ENABLE_CONTEXT_MEMORY = os.getenv("ENABLE_CONTEXT_MEMORY", "false").lower() == "true"
    MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "2000"))
    MAX_CONVERSATION_TURNS = int(os.getenv("MAX_CONVERSATION_TURNS", "15"))

    # Safety settings
    PII_DETECTION_ENABLED = os.getenv("PII_DETECTION_ENABLED", "false").lower() == "true"
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))

    # LLM settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "300"))
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
    LLM_LOG_FILE = os.getenv("LLM_LOG_FILE", "llm_interactions.log")

    @classmethod
    def validate(cls):
        """Validate configuration"""
        if cls.CONFIDENCE_THRESHOLD < 0 or cls.CONFIDENCE_THRESHOLD > 1:
            raise ValueError("CONFIDENCE_THRESHOLD must be between 0 and 1")
        if cls.MAX_INPUT_LENGTH <= 0:
            raise ValueError("MAX_INPUT_LENGTH must be positive")
        if cls.MAX_CONVERSATION_TURNS <= 0:
            raise ValueError("MAX_CONVERSATION_TURNS must be positive")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set")
        if cls.LLM_TEMPERATURE < 0 or cls.LLM_TEMPERATURE > 2:
            raise ValueError("LLM_TEMPERATURE must be between 0 and 2")
        if cls.LLM_MAX_TOKENS <= 0:
            raise ValueError("LLM_MAX_TOKENS must be positive")
        return True

    @classmethod
    def show(cls):
        """Display configuration"""
        print("\n=== Configuration ===")
        print(f"App: {cls.APP_NAME}")
        print(f"Environment: {cls.APP_ENVIRONMENT}")
        print(f"Debug: {cls.DEBUG}")
        print(f"Log File: {cls.LOG_FILE}")
        print(f"Context Memory: {cls.ENABLE_CONTEXT_MEMORY}")
        print(f"Max Input Length: {cls.MAX_INPUT_LENGTH}")
        print(f"Max Turns: {cls.MAX_CONVERSATION_TURNS}")
        print(f"Confidence Threshold: {cls.CONFIDENCE_THRESHOLD}")
        print("=" * 20 + "\n")


# Validate on import
Config.validate()

if __name__ == "__main__":
    Config.show()
