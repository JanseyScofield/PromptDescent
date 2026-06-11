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
    
    # New settings for batch processing and ID-based matching
    validation_json_path: str = "data/ground_truth.json"
    pdfs_directory: str = "documents"
    batch_size: int = 5
    history_file_path: str = "data/prompt_history.json"
    
    # AI Models
    extraction_model: str = "gpt-4o-mini"
    evaluation_model: str = "gpt-4o"
    max_document_length: int = 15000
    
    # model_config tells Pydantic to look for a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Instantiate settings (this immediately parses the .env file and validates types)
settings = AppSettings()

# Initialize OpenAI client securely using the validated key
client = OpenAI(api_key=settings.openai_api_key)
