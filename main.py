import os
from typing import List, Dict
from config.app_settings import settings
from services.data_loaders_service import DataLoaderService
from ai_agents.ai_agent import AIAgent
from ai_agents.openai_agent import OpenAIAgent

def run_prompt_gradient_descent(agent: AIAgent, loader: DataLoaderService, pdf_paths: List[str], ground_truth_dir: str) -> Dict[str, str]:
    print("Initializing Prompt Optimization Pipeline...")
    
    pdf_texts = loader.read_pdfs(pdf_paths)
    
    optimal_prompts = {}
    
    for pdf_path, document_text in pdf_texts.items():
        print(f"\n=========================================")
        print(f"Optimizing Prompt for: {pdf_path}")
        print(f"=========================================")
        
        pdf_filename = os.path.basename(pdf_path)
        pdf_name_without_ext, _ = os.path.splitext(pdf_filename)
        json_filename = f"{pdf_name_without_ext}.json"
        json_path = os.path.join(ground_truth_dir, json_filename)
        
        try:
            gt = loader.load_ground_truth(json_path)
        except Exception as e:
            print(f"Error loading ground truth from {json_path}: {e}")
            continue
            
        current_prompt = agent.generate_initial_prompt()
        print(f"\n[Iteration 0] Starting Prompt: {current_prompt}")
        
        for i in range(1, settings.max_iterations + 1):
            print(f"\n--- Iteration {i} ---")
            
            extracted_rules = agent.extract_rules(document_text, current_prompt)
            evaluation = agent.evaluate_extraction(extracted_rules, gt)
            
            print(f"Error Score: {evaluation.error_score}")
            print(f"Feedback (Gradient): {evaluation.feedback}")
            
            if evaluation.error_score <= settings.optimization_threshold:
                print(f"\n✅ Threshold reached! Optimal prompt found in {i} iterations.")
                break
                
            if i == settings.max_iterations:
                print(f"\n⚠️ Max iterations reached. Returning best prompt so far.")
                break
                
            print("Optimizing prompt based on feedback...")
            current_prompt = agent.optimize_prompt(current_prompt, evaluation)
            print(f"New Prompt: {current_prompt}")
            
        optimal_prompts[pdf_path] = current_prompt
        
    return optimal_prompts

if __name__ == "__main__":
    # Example execution
    # agent = OpenAIAgent()
    # loader = DataLoaderService()
    # run_prompt_gradient_descent(
    #     agent=agent,
    #     loader=loader,
    #     pdf_paths=["documents/sample_rules.pdf"],
    #     ground_truth_dir="data/ground_truths"
    # )
    pass