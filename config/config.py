# stocksage/config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages all application settings.
    It automatically reads from a .env file in the same directory as this file,
    or a specified path.
    """
    # Environment file configuration
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # API Keys
    GROQ_API_KEY: str

    # Agent Seeds
    API_GATEWAY_AGENT_SEED: str = "api_gateway_agent_seed_phrase_def_456"
    QUERY_PLANNER_AGENT_SEED: str = "query_planner_agent_seed_phrase_abc_123"
    FUNDAMENTALS_AGENT_SEED: str = "fundamentals_agent_seed_phrase_xyz_456"
    TECHNICAL_AGENT_SEED: str = "technical_agent_seed_phrase_ghi_789"
    SENTIMENT_AGENT_SEED: str = "sentiment_agent_seed_phrase_jkl_101"
    REPORT_COMPOSER_AGENT_SEED: str = "report_composer_agent_seed_mno_112"
    
    # Agent Addresses (to be populated in the .env file as they run)
    API_GATEWAY_ADDRESS: str | None = None
    QUERY_PLANNER_AGENT_ADDRESS: str | None = None
    FUNDAMENTALS_AGENT_ADDRESS: str | None = None
    TECHNICAL_AGENT_ADDRESS: str | None = None
    SENTIMENT_AGENT_ADDRESS: str | None = None
    REPORT_COMPOSER_AGENT_ADDRESS: str | None = None

    # Ports
    API_GATEWAY_PORT: int = 8100

# Create a single, importable instance of the settings
settings = Settings()