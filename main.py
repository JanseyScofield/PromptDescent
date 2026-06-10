import os
import json
import PyPDF2
from typing import List, Dict
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from openai import OpenAI

# ==========================================
# STEP 0: Configuration Management (Pydantic Settings)
# ==========================================
class AppSettings(BaseSettings):
    """
    Automatically loads and validates configuration from environment variables 
    or a local .env file.
    """
    openai_api_key: str
    optimization_threshold: float = 0.05
    max_iterations: int = 5
    
    # model_config tells Pydantic to look for a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Instantiate settings (this immediately parses the .env file and validates types)
settings = AppSettings()

# Initialize OpenAI client securely using the validated key
client = OpenAI(api_key=settings.openai_api_key)


# ==========================================
# STEP 3: Create Output Patterns (Pydantic)
# ==========================================
class ExtractedRules(BaseModel):
    documents_needed: List[str] = Field(description="List of required documents to start the process.")
    information_needed: List[str] = Field(description="List of specific information/data required to start the process.")

class EvaluationResult(BaseModel):
    error_score: float = Field(description="Error score between 0.0 (perfect match) and 1.0 (completely wrong).")
    feedback: str = Field(description="Detailed textual feedback on what the current extraction missed or hallucinated.")

class PromptUpdate(BaseModel):
    new_prompt: str = Field(description="The newly optimized prompt.")

# ==========================================
# STEP 1 & 2: Data Loaders
# ==========================================
def read_pdfs(pdf_paths: List[str]) -> str:
    combined_text = ""
    for path in pdf_paths:
        try:
            with open(path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    combined_text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading {path}: {e}")
    return combined_text

def load_ground_truth(json_path: str) -> Dict:
    with open(json_path, 'r') as file:
        return json.load(file)

# ==========================================
# STEP 4: Rule Extractor AI
# ==========================================
def extract_rules(document_text: str, current_prompt: str) -> ExtractedRules:
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

# ==========================================
# STEP 5: Evaluator AI (Gradient)import os
import json
import PyPDF2
from typing import List, Dict
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from openai import OpenAI

# ==========================================
# STEP 0: Configuration Management (Pydantic Settings)
# ==========================================
class AppSettings(BaseSettings):
    """
    Automatically loads and validates configuration from environment variables 
    or a local .env file.
    """
    openai_api_key: str
    optimization_threshold: float = 0.05
    max_iterations: int = 5
    
    # model_config tells Pydantic to look for a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Instantiate settings (this immediately parses the .env file and validates types)
settings = AppSettings()

# Initialize OpenAI client securely using the validated key
client = OpenAI(api_key=settings.openai_api_key)


# ==========================================
# STEP 3: Create Output Patterns (Pydantic)
# ==========================================
class ExtractedRules(BaseModel):
    documents_needed: List[str] = Field(description="List of required documents to start the process.")
    information_needed: List[str] = Field(description="List of specific information/data required to start the process.")

class EvaluationResult(BaseModel):
    error_score: float = Field(description="Error score between 0.0 (perfect match) and 1.0 (completely wrong).")
    feedback: str = Field(description="Detailed textual feedback on what the current extraction missed or hallucinated.")

class PromptUpdate(BaseModel):
    new_prompt: str = Field(description="The newly optimized prompt.")

# ==========================================
# STEP 1 & 2: Data Loaders
# ==========================================
def read_pdfs(pdf_paths: List[str]) -> str:
    combined_text = ""
    for path in pdf_paths:
        try:
            with open(path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    combined_text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading {path}: {e}")
    return combined_text

def load_ground_truth(json_path: str) -> Dict:
    with open(json_path, 'r') as file:
        return json.load(file)

# ==========================================
# STEP 4: Rule Extractor AI
# ==========================================
def extract_rules(document_text: str, current_prompt: str) -> ExtractedRules:
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

# ==========================================
# STEP 5: Evaluator AI (Gradient)
# ==========================================
def evaluate_extraction(ai_answers: ExtractedRules, ground_truth: Dict) -> EvaluationResult:
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

# ==========================================
# STEP 6: Rogue Seed AI
# ==========================================
def generate_initial_prompt() -> str:
    return (
        "You are a strict data extraction AI. Read the provided text and identify "
        "exactly what documents and pieces of information are required for the process to begin."
    )

# ==========================================
# STEP 7: Prompt Optimizer AI
# ==========================================
def optimize_prompt(current_prompt: str, evaluation: EvaluationResult) -> str:
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

# ==========================================
# MAIN: The Gradient Descent Loop
# ==========================================
def run_prompt_gradient_descent(pdf_paths: List[str], ground_truth_path: str):
    print("Initializing Prompt Optimization Pipeline...")
    
    document_text = read_pdfs(pdf_paths)
    ground_truth = load_ground_truth(ground_truth_path)
    
    current_prompt = generate_initial_prompt()
    print(f"\n[Iteration 0] Starting Prompt: {current_prompt}")
    
    # Using the globally loaded settings for hyperparameters
    for i in range(1, settings.max_iterations + 1):
        print(f"\n--- Iteration {i} ---")
        
        extracted_rules = extract_rules(document_text, current_prompt)
        evaluation = evaluate_extraction(extracted_rules, ground_truth)
        
        print(f"Error Score: {evaluation.error_score}")
        print(f"Feedback (Gradient): {evaluation.feedback}")
        
        if evaluation.error_score <= settings.optimization_threshold:
            print(f"\n✅ Threshold reached! Optimal prompt found in {i} iterations.")
            break
            
        if i == settings.max_iterations:
            print(f"\n⚠️ Max iterations reached. Returning best prompt so far.")
            break
            
        print("Optimizing prompt based on feedback...")
        current_prompt = optimize_prompt(current_prompt, evaluation)
        print(f"New Prompt: {current_prompt}")
        
    return current_prompt

if __name__ == "__main__":
    # Example execution
    # run_prompt_gradient_descent(
    #     pdf_paths=["documents/sample_rules.pdf"],
    #     ground_truth_path="data/ground_truth.json"
    # )
    passimport os
import json
import PyPDF2
from typing import List, Dict
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from openai import OpenAI

# ==========================================
# STEP 0: Configuration Management (Pydantic Settings)
# ==========================================
class AppSettings(BaseSettings):
    """
    Automatically loads and validates configuration from environment variables 
    or a local .env file.
    """
    openai_api_key: str
    optimization_threshold: float = 0.05
    max_iterations: int = 5
    
    # model_config tells Pydantic to look for a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Instantiate settings (this immediately parses the .env file and validates types)
settings = AppSettings()

# Initialize OpenAI client securely using the validated key
client = OpenAI(api_key=settings.openai_api_key)


# ==========================================
# STEP 3: Create Output Patterns (Pydantic)
# ==========================================
class ExtractedRules(BaseModel):
    documents_needed: List[str] = Field(description="List of required documents to start the process.")
    information_needed: List[str] = Field(description="List of specific information/data required to start the process.")

class EvaluationResult(BaseModel):
    error_score: float = Field(description="Error score between 0.0 (perfect match) and 1.0 (completely wrong).")
    feedback: str = Field(description="Detailed textual feedback on what the current extraction missed or hallucinated.")

class PromptUpdate(BaseModel):
    new_prompt: str = Field(description="The newly optimized prompt.")

# ==========================================
# STEP 1 & 2: Data Loaders
# ==========================================
def read_pdfs(pdf_paths: List[str]) -> str:
    combined_text = ""
    for path in pdf_paths:
        try:
            with open(path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    combined_text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading {path}: {e}")
    return combined_text

def load_ground_truth(json_path: str) -> Dict:
    with open(json_path, 'r') as file:
        return json.load(file)

# ==========================================
# STEP 4: Rule Extractor AI
# ==========================================
def extract_rules(document_text: str, current_prompt: str) -> ExtractedRules:
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

# ==========================================
# STEP 5: Evaluator AI (Gradient)
# ==========================================
def evaluate_extraction(ai_answers: ExtractedRules, ground_truth: Dict) -> EvaluationResult:
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

# ==========================================
# STEP 6: Rogue Seed AI
# ==========================================
def generate_initial_prompt() -> str:
    return (
        "You are a strict data extraction AI. Read the provided text and identify "
        "exactly what documents and pieces of information are required for the process to begin."
    )

# ==========================================
# STEP 7: Prompt Optimizer AI
# ==========================================
def optimize_prompt(current_prompt: str, evaluation: EvaluationResult) -> str:
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

# ==========================================
# MAIN: The Gradient Descent Loop
# ==========================================
def run_prompt_gradient_descent(pdf_paths: List[str], ground_truth_path: str):
    print("Initializing Prompt Optimization Pipeline...")
    
    document_text = read_pdfs(pdf_paths)
    ground_truth = load_ground_truth(ground_truth_path)
    
    current_prompt = generate_initial_prompt()
    print(f"\n[Iteration 0] Starting Prompt: {current_prompt}")
    
    # Using the globally loaded settings for hyperparameters
    for i in range(1, settings.max_iterations + 1):
        print(f"\n--- Iteration {i} ---")
        
        extracted_rules = extract_rules(document_text, current_prompt)
        evaluation = evaluate_extraction(extracted_rules, ground_truth)
        
        print(f"Error Score: {evaluation.error_score}")
        print(f"Feedback (Gradient): {evaluation.feedback}")
        
        if evaluation.error_score <= settings.optimization_threshold:
            print(f"\n✅ Threshold reached! Optimal prompt found in {i} iterations.")
            break
            
        if i == settings.max_iterations:
            print(f"\n⚠️ Max iterations reached. Returning best prompt so far.")
            break
            
        print("Optimizing prompt based on feedback...")
        current_prompt = optimize_prompt(current_prompt, evaluation)
        print(f"New Prompt: {current_prompt}")
        
    return current_prompt

if __name__ == "__main__":
    # Example execution
    # run_prompt_gradient_descent(
    #     pdf_paths=["documents/sample_rules.pdf"],
    #     ground_truth_path="data/ground_truth.json"
    # )
    passimport os
import json
import PyPDF2
from typing import List, Dict
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from openai import OpenAI

# ==========================================
# STEP 0: Configuration Management (Pydantic Settings)
# ==========================================
class AppSettings(BaseSettings):
    """
    Automatically loads and validates configuration from environment variables 
    or a local .env file.
    """
    openai_api_key: str
    optimization_threshold: float = 0.05
    max_iterations: int = 5
    
    # model_config tells Pydantic to look for a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Instantiate settings (this immediately parses the .env file and validates types)
settings = AppSettings()

# Initialize OpenAI client securely using the validated key
client = OpenAI(api_key=settings.openai_api_key)


# ==========================================
# STEP 3: Create Output Patterns (Pydantic)
# ==========================================
class ExtractedRules(BaseModel):
    documents_needed: List[str] = Field(description="List of required documents to start the process.")
    information_needed: List[str] = Field(description="List of specific information/data required to start the process.")

class EvaluationResult(BaseModel):
    error_score: float = Field(description="Error score between 0.0 (perfect match) and 1.0 (completely wrong).")
    feedback: str = Field(description="Detailed textual feedback on what the current extraction missed or hallucinated.")

class PromptUpdate(BaseModel):
    new_prompt: str = Field(description="The newly optimized prompt.")

# ==========================================
# STEP 1 & 2: Data Loaders
# ==========================================
def read_pdfs(pdf_paths: List[str]) -> str:
    combined_text = ""
    for path in pdf_paths:
        try:
            with open(path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    combined_text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading {path}: {e}")
    return combined_text

def load_ground_truth(json_path: str) -> Dict:
    with open(json_path, 'r') as file:
        return json.load(file)

# ==========================================
# STEP 4: Rule Extractor AI
# ==========================================
def extract_rules(document_text: str, current_prompt: str) -> ExtractedRules:
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

# ==========================================
# STEP 5: Evaluator AI (Gradient)
# ==========================================
def evaluate_extraction(ai_answers: ExtractedRules, ground_truth: Dict) -> EvaluationResult:
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

# ==========================================
# STEP 6: Rogue Seed AI
# ==========================================
def generate_initial_prompt() -> str:
    return (
        "You are a strict data extraction AI. Read the provided text and identify "
        "exactly what documents and pieces of information are required for the process to begin."
    )

# ==========================================
# STEP 7: Prompt Optimizer AI
# ==========================================
def optimize_prompt(current_prompt: str, evaluation: EvaluationResult) -> str:
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

# ==========================================
# MAIN: The Gradient Descent Loop
# ==========================================
def run_prompt_gradient_descent(pdf_paths: List[str], ground_truth_path: str):
    print("Initializing Prompt Optimization Pipeline...")
    
    document_text = read_pdfs(pdf_paths)
    ground_truth = load_ground_truth(ground_truth_path)
    
    current_prompt = generate_initial_prompt()
    print(f"\n[Iteration 0] Starting Prompt: {current_prompt}")
    
    # Using the globally loaded settings for hyperparameters
    for i in range(1, settings.max_iterations + 1):
        print(f"\n--- Iteration {i} ---")
        
        extracted_rules = extract_rules(document_text, current_prompt)
        evaluation = evaluate_extraction(extracted_rules, ground_truth)
        
        print(f"Error Score: {evaluation.error_score}")
        print(f"Feedback (Gradient): {evaluation.feedback}")
        
        if evaluation.error_score <= settings.optimization_threshold:
            print(f"\n✅ Threshold reached! Optimal prompt found in {i} iterations.")
            break
            
        if i == settings.max_iterations:
            print(f"\n⚠️ Max iterations reached. Returning best prompt so far.")
            break
            
        print("Optimizing prompt based on feedback...")
        current_prompt = optimize_prompt(current_prompt, evaluation)
        print(f"New Prompt: {current_prompt}")
        
    return current_prompt

if __name__ == "__main__":
    # Example execution
    # run_prompt_gradient_descent(
    #     pdf_paths=["documents/sample_rules.pdf"],
    #     ground_truth_path="data/ground_truth.json"
    # )
    pass
# ==========================================
def evaluate_extraction(ai_answers: ExtractedRules, ground_truth: Dict) -> EvaluationResult:
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

# ==========================================
# STEP 6: Rogue Seed AI
# ==========================================
def generate_initial_prompt() -> str:
    return (
        "You are a strict data extraction AI. Read the provided text and identify "
        "exactly what documents and pieces of information are required for the process to begin."
    )

# ==========================================
# STEP 7: Prompt Optimizer AI
# ==========================================
def optimize_prompt(current_prompt: str, evaluation: EvaluationResult) -> str:
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

# ==========================================
# MAIN: The Gradient Descent Loop
# ==========================================
def run_prompt_gradient_descent(pdf_paths: List[str], ground_truth_path: str):
    print("Initializing Prompt Optimization Pipeline...")
    
    document_text = read_pdfs(pdf_paths)
    ground_truth = load_ground_truth(ground_truth_path)
    
    current_prompt = generate_initial_prompt()
    print(f"\n[Iteration 0] Starting Prompt: {current_prompt}")
    
    # Using the globally loaded settings for hyperparameters
    for i in range(1, settings.max_iterations + 1):
        print(f"\n--- Iteration {i} ---")
        
        extracted_rules = extract_rules(document_text, current_prompt)
        evaluation = evaluate_extraction(extracted_rules, ground_truth)
        
        print(f"Error Score: {evaluation.error_score}")
        print(f"Feedback (Gradient): {evaluation.feedback}")
        
        if evaluation.error_score <= settings.optimization_threshold:
            print(f"\n✅ Threshold reached! Optimal prompt found in {i} iterations.")
            break
            
        if i == settings.max_iterations:
            print(f"\n⚠️ Max iterations reached. Returning best prompt so far.")
            break
            
        print("Optimizing prompt based on feedback...")
        current_prompt = optimize_prompt(current_prompt, evaluation)
        print(f"New Prompt: {current_prompt}")
        
    return current_prompt

if __name__ == "__main__":
    # Example execution
    # run_prompt_gradient_descent(
    #     pdf_paths=["documents/sample_rules.pdf"],
    #     ground_truth_path="data/ground_truth.json"
    # )
    pass