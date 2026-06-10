from pydantic_settings import BaseSettings, SettingsConfigDict
from openai import OpenAI

class AppSettings(BaseSettings):
    """
    Automatically loads and validates configuration from environment variables 
    or a local .env file.
    """
    openai_api_key: str
    optimization_threshold: float = 0.05
    max_iterations: int = 5
    
    # model_config tells Pydantic to look for a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Instantiate settings (this immediately parses the .env file and validates types)
settings = AppSettings()

# Initialize OpenAI client securely using the validated key
client = OpenAI(api_key=settings.openai_api_key)
