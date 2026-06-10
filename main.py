import os
from typing import List, Dict
from config.app_settings import settings
from services.data_loaders_service import DataLoaderService
from models.evaluation_results import EvaluationResult
from ai_agents.ai_agent import AIAgent
from ai_agents.openai_agent import OpenAIAgent

def run_prompt_gradient_descent(agent: AIAgent, loader: DataLoaderService, pdf_paths: List[str], ground_truth_dir: str) -> str:
    print("Initializing Prompt Optimization Pipeline...")
    pdf_texts = loader.read_pdfs(pdf_paths)
    current_prompt = agent.generate_initial_prompt()
    best_score = 0.0
    best_prompt = current_prompt

    print(f"\n[Iteration 0] Starting Prompt: {current_prompt}")
    
    for i in range(1, settings.max_iterations + 1):
        print(f"\n--- Iteration {i} ---")
        
        errors = []
        feedbacks = []
        
        for pdf_path, document_text in pdf_texts.items():
            pdf_filename = os.path.basename(pdf_path)
            pdf_name_without_ext, _ = os.path.splitext(pdf_filename)
            json_filename = f"{pdf_name_without_ext}.json"
            json_path = os.path.join(ground_truth_dir, json_filename)
            
            try:
                gt = loader.load_ground_truth(json_path)
            except Exception as e:
                print(f"Error loading ground truth from {json_path}: {e}")
                continue
                
            extracted_rules = agent.extract_rules(document_text, current_prompt)
            evaluation = agent.evaluate_extraction(extracted_rules, gt)
            
            errors.append(evaluation.error_score)
            
            if evaluation.error_score > 0.0:
                feedbacks.append(f"PDF [{pdf_filename}]: {evaluation.feedback}")
                
        if not errors:
            print("No valid PDFs/Ground Truths were successfully evaluated.")
            break
            
        average_error_score = sum(errors) / len(errors)
        print(f"Average Error Score: {average_error_score:.4f}")
        
        if feedbacks:
            combined_feedback = "\n".join(feedbacks)
        else:
            combined_feedback = "No errors detected on any document."
            
        if average_error_score <= settings.optimization_threshold:
            print(f"\n✅ Threshold reached! Optimal prompt found in {i} iterations.")
            break
            
        if i == settings.max_iterations:
            print(f"\n⚠️ Max iterations reached. Returning best prompt so far.")
            break
            
        print("Optimizing prompt based on aggregated feedback...")
        
        aggregated_evaluation = EvaluationResult(
            error_score=average_error_score,
            feedback=combined_feedback
        )
        
        current_prompt = agent.optimize_prompt(current_prompt, aggregated_evaluation)
        print(f"New Prompt: {current_prompt}")

        if average_error_score > best_score:
            best_score = average_error_score
            best_prompt = current_prompt
        
    return best_prompt + f"\nThe error score achieved with this prompt is {best_score}"

if __name__ == "__main__":
    # Example execution
    # agent = OpenAIAgent()
    # loader = DataLoaderService()
    # run_prompt_gradient_descent(
    #     agent=agent,
    #     loader=loader,
    #     pdf_paths=["documents/rules_1.pdf", "documents/rules_2.pdf"],
    #     ground_truth_dir="data/ground_truths"
    # )
    pass