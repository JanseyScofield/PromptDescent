from abc import ABC, abstractmethod
from typing import Dict
from models.extracted_rules import ExtractedRules
from models.evaluation_results import EvaluationResult

class AIAgent(ABC):
    @abstractmethod
    def extract_rules(self, document_text: str, current_prompt: str) -> ExtractedRules:
        """
        Extract rules from the document text based on the current prompt.
        """
        pass

    @abstractmethod
    def evaluate_extraction(self, ai_answers: ExtractedRules, ground_truth: Dict) -> EvaluationResult:
        """
        Evaluate the extracted rules against the ground truth.
        """
        pass

    @abstractmethod
    def generate_initial_prompt(self) -> str:
        """
        Generate the initial prompt for the extraction process.
        """
        pass

    @abstractmethod
    def optimize_prompt(self, current_prompt: str, evaluation: EvaluationResult) -> str:
        """
        Optimize the prompt based on the evaluation result.
        """
        pass
