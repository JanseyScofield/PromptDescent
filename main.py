from typing import List
from config.app_settings import settings
from services.data_loaders_service import DataLoaderService
from ai_agents.ai_agent import AIAgent
from ai_agents.openai_agent import OpenAIAgent

def run_prompt_gradient_descent(agent: AIAgent, loader: DataLoaderService, pdf_paths: List[str], ground_truth_path: str) -> str:
    print("Initializing Prompt Optimization Pipeline...")
    
    document_text = loader.read_pdfs(pdf_paths)
    ground_truth = loader.load_ground_truth(ground_truth_path)
    
    current_prompt = agent.generate_initial_prompt()
    print(f"\n[Iteration 0] Starting Prompt: {current_prompt}")
    
    for i in range(1, settings.max_iterations + 1):
        print(f"\n--- Iteration {i} ---")
        
        extracted_rules = agent.extract_rules(document_text, current_prompt)
        evaluation = agent.evaluate_extraction(extracted_rules, ground_truth)
        
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
        
    return current_prompt

if __name__ == "__main__":
    # Example execution
    # agent = OpenAIAgent()
    # loader = DataLoaderService()
    # run_prompt_gradient_descent(
    #     agent=agent,
    #     loader=loader,
    #     pdf_paths=["documents/sample_rules.pdf"],
    #     ground_truth_path="data/ground_truth.json"
    # )
    pass