from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    """
    Automatically loads and validates configuration from environment variables 
    or a local .env file.
    """
    gemini_api_key: str
    openai_api_key: Optional[str] = None
    ollama_host: str = "http://localhost:11434"
    optimization_threshold: float = 0.05
    max_iterations: int = 5
    
    # New settings for batch processing and ID-based matching
    validation_json_path: str = "data/ground_truth.json"
    pdfs_directory: str = "data/documents"
    batch_size: int = 5
    max_files: Optional[int] = None
    history_file_path: str = "data/prompt_history.json"
    
    # Gemini AI Models
    gemini_extraction_model: str = "gemini-1.5-flash"
    gemini_evaluation_model: str = "gemini-1.5-pro"
    
    # OpenAI AI Models
    openai_extraction_model: str = "gpt-4o-mini"
    openai_evaluation_model: str = "gpt-4o"
    
    # Ollama AI Models
    ollama_extraction_model: str = "llama3"
    ollama_evaluation_model: str = "llama3"
    
    max_document_length: int = 30000  # Gemini has larger context
    
    # Legacy / Default (to maintain compatibility if needed)
    extraction_model: str = "gemini-1.5-flash"
    evaluation_model: str = "gemini-1.5-pro"
    
    # model_config tells Pydantic to look for a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Instantiate settings
settings = AppSettings()
