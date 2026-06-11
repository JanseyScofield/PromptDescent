from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    """
    Automatically loads and validates configuration from environment variables 
    or a local .env file.
    """
    gemini_api_key: str
    optimization_threshold: float = 0.05
    max_iterations: int = 5
    
    # New settings for batch processing and ID-based matching
    validation_json_path: str = "data/ground_truth.json"
    pdfs_directory: str = "data/documents"
    batch_size: int = 5
    max_files: Optional[int] = None
    history_file_path: str = "data/prompt_history.json"
    
    # AI Models
    extraction_model: str = "gemini-1.5-flash"
    evaluation_model: str = "gemini-1.5-pro"
    max_document_length: int = 30000  # Gemini has larger context
    
    # model_config tells Pydantic to look for a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Instantiate settings
settings = AppSettings()
