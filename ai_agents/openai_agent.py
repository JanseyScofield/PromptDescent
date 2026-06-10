import json
from typing import Dict
from config.app_settings import client, settings
from models.extracted_rules import ExtractedRules
from models.evaluation_results import EvaluationResult
from models.prompt_update import PromptUpdate
from ai_agents.ai_agent import AIAgent

class OpenAIAgent(AIAgent):
    def extract_rules(self, document_text: str, current_prompt: str) -> ExtractedRules:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": current_prompt},
                {"role": "user", "content": f"Extract rules from:\n\n{document_text[:10000]}"}
            ],
            response_format=ExtractedRules,
            temperature=0.0 
        )
        return response.choices[0].message.parsed

    def evaluate_extraction(self, ai_answers: ExtractedRules, ground_truth: Dict) -> EvaluationResult:
        system_prompt = """
        You are an expert evaluator. Compare the AI's extracted rules with the Ground Truth.
        Calculate an error score from 0.0 (perfect) to 1.0 (completely wrong). 
        Provide strict, detailed feedback on what is missing or incorrect.
        """
        user_content = f"Ground Truth:\n{json.dumps(ground_truth)}\n\nAI Extraction:\n{ai_answers.model_dump_json()}"
        
        response = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format=EvaluationResult,
            temperature=0.0
        )
        return response.choices[0].message.parsed

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
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format=PromptUpdate,
            temperature=0.7 
        )
        return response.choices[0].message.parsed.new_prompt
