import json
from typing import Dict, Optional
from config.app_settings import client, settings
from models.extracted_rules import ExtractedRules
from models.evaluation_results import EvaluationResult
from models.prompt_update import PromptUpdate
from ai_agents.ai_agent import AIAgent

class OpenAIAgent(AIAgent):
    def extract_rules(self, document_text: str, current_prompt: str) -> Optional[ExtractedRules]:
        try:
            response = client.beta.chat.completions.parse(
                model=settings.extraction_model,
                messages=[
                    {"role": "system", "content": current_prompt},
                    {"role": "user", "content": f"Extract rules from:\n\n{document_text[:settings.max_document_length]}"}
                ],
                response_format=ExtractedRules,
                temperature=0.0 
            )
            return response.choices[0].message.parsed
        except Exception as e:
            print(f"Error during API extraction: {e}")
            return None

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
        
        try:
            response = client.beta.chat.completions.parse(
                model=settings.evaluation_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format=EvaluationResult,
                temperature=0.0
            )
            return response.choices[0].message.parsed
        except Exception as e:
            print(f"Error during API evaluation: {e}")
            return None

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
        
        response = client.beta.chat.completions.parse(
            model=settings.evaluation_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format=PromptUpdate,
            temperature=0.7 
        )
        return response.choices[0].message.parsed.new_prompt
