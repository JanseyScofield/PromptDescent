import json
import logging
from google import genai
from typing import Dict, Optional, Type, Any
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from config.app_settings import settings
from models.extracted_rules import ExtractedRules
from models.evaluation_results import EvaluationResult
from models.prompt_update import PromptUpdate
from ai_agents.ai_agent import AIAgent

# Configure logging for tenacity retries
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiAgent(AIAgent):
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.extraction_model = settings.extraction_model
        self.evaluation_model = settings.evaluation_model

    @retry(
        stop=stop_after_attempt(6), 
        wait=wait_exponential(multiplier=5, min=10, max=70), 
        reraise=True,
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def _call_api_with_retry(self, model_id: str, system_prompt: str, user_content: str, response_schema: Type[BaseModel]):
        return self.client.models.generate_content(
            model=model_id,
            contents=user_content,
            config={
                'system_instruction': system_prompt,
                'response_mime_type': 'application/json',
                'response_schema': response_schema,
            }
        )

    def _generate_structured_output(self, model_id: str, system_prompt: str, user_content: str, response_schema: Type[BaseModel]) -> Optional[Any]:
        try:
            # Gemini structured outputs using google-genai SDK
            response = self._call_api_with_retry(model_id, system_prompt, user_content, response_schema)
            
            # The SDK can return a parsed object if response_schema is provided, 
            # but using model_validate_json ensures consistency with Pydantic 2.
            return response_schema.model_validate_json(response.text)
        except Exception as e:
            print(f"Error during Gemini API call: {e}")
            return None

    def extract_rules(self, document_text: str, current_prompt: str) -> Optional[ExtractedRules]:
        user_content = f"Extract rules from:\n\n{document_text[:settings.max_document_length]}"
        return self._generate_structured_output(
            self.extraction_model,
            current_prompt,
            user_content,
            ExtractedRules
        )

    def evaluate_extraction(self, ai_answers: ExtractedRules, ground_truth: Dict, document_text: str) -> Optional[EvaluationResult]:
        system_prompt = """
        You are an expert evaluator. Compare the AI's extracted rules with the Ground Truth.
        You also have access to the ORIGINAL DOCUMENT TEXT to understand WHY the AI succeeded or failed.
        
        The rules follow this format:
        - documents_needed: List of required physical or digital documents.
        - information_needed: List of specific data points or information fields.
        
        Calculate an error score from 0.0 (perfect match) to 1.0 (completely wrong). 
        Provide strict, detailed feedback. If the AI missed something that IS in the document but NOT in the extraction, 
        explain where in the document it can be found so the prompt can be improved.
        """
        user_content = (
            f"ORIGINAL DOCUMENT TEXT (Excerpt):\n{document_text[:settings.max_document_length]}\n\n"
            f"GROUND TRUTH (Target):\n{json.dumps(ground_truth)}\n\n"
            f"AI EXTRACTION (Current):\n{ai_answers.model_dump_json()}"
        )
        return self._generate_structured_output(
            self.evaluation_model,
            system_prompt,
            user_content,
            EvaluationResult
        )

    def generate_initial_prompt(self) -> str:
        return (
            "You are a strict data extraction AI. Read the provided text and identify "
            "exactly what documents and pieces of information are required for the process to begin."
        )

    def optimize_prompt(self, current_prompt: str, evaluation: EvaluationResult) -> str:
        system_prompt = """
        You are a Prompt Engineering Expert. Your goal is to improve an extraction prompt.
        You will be given the current prompt, its error score, and feedback on why it failed.
        Rewrite the prompt to fix these issues. Make it robust, explicit, and concise.
        """
        user_content = f"Current Prompt:\n{current_prompt}\n\nError Score: {evaluation.error_score}\n\nFeedback:\n{evaluation.feedback}"
        
        result = self._generate_structured_output(
            self.evaluation_model,
            system_prompt,
            user_content,
            PromptUpdate
        )
        return result.new_prompt if result else current_prompt
