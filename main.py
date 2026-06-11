import os
import json
import argparse
from datetime import datetime
from typing import List, Dict
from config.app_settings import settings
from services.data_loaders_service import DataLoaderService
from models.evaluation_results import EvaluationResult
from ai_agents.ai_agent import AIAgent
from ai_agents.gemini_agent import GeminiAgent

def run_prompt_gradient_descent(agent: AIAgent, loader: DataLoaderService, enable_logging: bool = False) -> str:
    """
    Orchestrates the prompt optimization process using a gradient descent approach.
    Now supports mini-batch processing, ID-based matching, and epoch-based history tracking.
    """
    def log(msg: str):
        if enable_logging:
            print(f"[LOG] {msg}")

    print("Initializing Prompt Optimization Pipeline...")
    
    # 1. Load mappings and ground truths
    pdf_mapping = loader.map_pdfs_by_id(settings.pdfs_directory)
    try:
        all_ground_truths = loader.load_ground_truth(settings.validation_json_path)
    except Exception as e:
        return f"Critical Error: Could not load ground truth JSON: {e}"

    if not pdf_mapping:
        return "Critical Error: No PDF files found in the specified directory."

    current_prompt = agent.generate_initial_prompt()
    best_score = float('inf')  # In error score, lower is better. Initializing with infinity.
    best_prompt = current_prompt

    print(f"\n[Iteration 0] Starting Prompt: {current_prompt}")
    
    # List of IDs to process (sorted for predictability)
    pdf_ids = sorted(list(pdf_mapping.keys()), key=lambda x: int(x) if x.isdigit() else x)
    
    # Apply file limit if configured
    if settings.max_files is not None:
        pdf_ids = pdf_ids[:settings.max_files]
        log(f"Limiting universe to the first {settings.max_files} IDs: {pdf_ids}")

    prompt_history = []

    # Ensure history directory exists
    history_dir = os.path.dirname(settings.history_file_path)
    if history_dir and not os.path.exists(history_dir):
        os.makedirs(history_dir)
    
    for i in range(1, settings.max_iterations + 1):
        print(f"\n--- Iteration (Epoch) {i} ---")
        
        epoch_errors = []
        epoch_feedbacks = []
        
        # 2. Split IDs into batches
        for start_idx in range(0, len(pdf_ids), settings.batch_size):
            batch_ids = pdf_ids[start_idx : start_idx + settings.batch_size]
            log(f"Processing batch ({start_idx // settings.batch_size + 1}): {batch_ids}")
            
            for file_id in batch_ids:
                pdf_path = pdf_mapping[file_id]
                pdf_filename = os.path.basename(pdf_path)
                
                # Get ground truth for this ID
                gt = all_ground_truths.get(file_id)
                if not gt:
                    log(f"Skipping {pdf_filename}: No ground truth found for ID '{file_id}'")
                    continue
                
                # Extract text
                log(f"Reading PDF for ID [{file_id}]: {pdf_filename}")
                document_text = loader.read_pdf(pdf_path)
                if not document_text:
                    continue
                
                # Step 3: Extract and Validate (with PDF context)
                log(f"Running Extraction for ID [{file_id}]...")
                extracted_rules = agent.extract_rules(document_text, current_prompt)
                if not extracted_rules:
                    log(f"Skipping {pdf_filename}: Extraction API failed.")
                    continue
                
                log(f"Running Evaluation for ID [{file_id}]...")
                evaluation = agent.evaluate_extraction(extracted_rules, gt, document_text)
                if not evaluation:
                    log(f"Skipping {pdf_filename}: Evaluation API failed.")
                    continue
                
                epoch_errors.append(evaluation.error_score)
                
                if evaluation.error_score > 0.0:
                    epoch_feedbacks.append(f"PDF ID [{file_id}]: {evaluation.feedback}")
        
        if not epoch_errors:
            print("No valid PDFs were successfully evaluated in this iteration.")
            break
            
        average_error_score = sum(epoch_errors) / len(epoch_errors)
        print(f"Iteration Average Error Score: {average_error_score:.4f}")
        
        # 3. Prompt Memory: Save checkpoint
        epoch_data = {
            "epoch": i,
            "prompt": current_prompt,
            "average_error_score": average_error_score,
            "feedbacks": epoch_feedbacks,
            "timestamp": datetime.now().isoformat()
        }
        prompt_history.append(epoch_data)
        
        try:
            with open(settings.history_file_path, "w", encoding="utf-8") as f:
                json.dump(prompt_history, f, indent=4, ensure_ascii=False)
            log(f"Epoch {i} history saved to {settings.history_file_path}")
        except Exception as e:
            print(f"Error saving history: {e}")

        if average_error_score < best_score:
            best_score = average_error_score
            best_prompt = current_prompt
            
        if average_error_score <= settings.optimization_threshold:
            print(f"\n✅ Threshold reached! Optimal prompt found in {i} iterations.")
            break
            
        if i == settings.max_iterations:
            print(f"\n⚠️ Max iterations reached. Returning best prompt.")
            break
            
        # Step 4: Aggregate and Optimize (End of Epoch)
        print("Optimizing prompt based on aggregated feedback from all batches...")
        combined_feedback = "\n".join(epoch_feedbacks) if epoch_feedbacks else "General refinement needed."
        
        aggregated_evaluation = EvaluationResult(
            error_score=average_error_score,
            feedback=combined_feedback
        )
        
        current_prompt = agent.optimize_prompt(current_prompt, aggregated_evaluation)
        log(f"New Prompt: {current_prompt}")
        
    return best_prompt + f"\n\nFinal error score achieved: {best_score:.4f}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Prompt Optimization Gradient Descent.")
    parser.add_argument("--log", action="store_true", help="Enable verbose logging during execution.")
    parser.add_argument("--max-files", type=int, help="Maximum number of IDs to process.")
    args = parser.parse_args()

    if args.max_files is not None:
        settings.max_files = args.max_files

    agent = GeminiAgent()
    loader = DataLoaderService()
    
    result = run_prompt_gradient_descent(agent, loader, enable_logging=args.log)
    
    print("\n" + "="*30)
    print("FINAL RESULT:")
    print(result)
