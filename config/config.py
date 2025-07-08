from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    """
    Manages application settings, loading from environment variables or a .env file.
    """
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # --- Agent Seeds ---
    API_GATEWAY_AGENT_SEED: str = os.getenv("API_GATEWAY_AGENT_SEED", "default_api_gateway_seed")
    QUERY_PLANNER_AGENT_SEED: str = os.getenv("QUERY_PLANNER_AGENT_SEED", "default_query_planner_seed")
    FUNDAMENTALS_AGENT_SEED: str = os.getenv("FUNDAMENTALS_AGENT_SEED", "default_fundamentals_seed")
    TECHNICAL_AGENT_SEED: str = "technical_agent_seed_phrase_ghi_789"
    SENTIMENT_AGENT_SEED: str = "sentiment_agent_seed_phrase_jkl_101"
    REPORT_COMPOSER_AGENT_SEED: str = "report_composer_agent_seed_mno_112"
    
    # --- Agent Addresses (for inter-agent communication) ---
    API_GATEWAY_AGENT_ADDRESS: str | None = None
    QUERY_PLANNER_AGENT_ADDRESS: str | None = None
    FUNDAMENTALS_AGENT_ADDRESS: str | None = None
    TECHNICAL_AGENT_ADDRESS: str | None = None
    SENTIMENT_AGENT_ADDRESS: str | None = None
    REPORT_COMPOSER_AGENT_ADDRESS: str | None = None

    # --- Service Ports ---
    API_GATEWAY_PORT: int = 8100

    # --- External API Keys ---
    GROQ_API_KEY: str

# Create a single, importable instance of the settings
settings = Settings()