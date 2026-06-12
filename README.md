# Prompt Descent Optimization Pipeline

An automated prompt optimization pipeline inspired by gradient descent. This project refines a **single** global System Prompt iteratively across a batch of multiple PDF documents to find the best prompt that satisfies all documents simultaneously. It supports **OpenAI**, **Gemini**, and **Ollama** agents! It evaluates the outputs of all documents in each iteration (epoch) against a ground truth JSON, computing an average error score and combining feedback to guide the prompt optimizer.

---

## 🏗️ Architecture & Project Structure

The project features a modular, clean, and decoupled architecture, now supporting multiple LLM backends:

```text
prompt-descent/
├── config/
│   ├── __init__.py
│   └── app_settings.py          # Handles app configurations (Pydantic Settings)
├── models/
│   ├── __init__.py
│   ├── extracted_rules.py       # Pydantic Model for rule extraction structure (ExtractedRules)
│   ├── evaluation_results.py    # Pydantic Model for feedback and error scoring (EvaluationResult)
│   └── prompt_update.py         # Pydantic Model for optimized prompt updates (PromptUpdate)
├── services/
│   ├── __init__.py
│   └── data_loaders_service.py  # Handles loading PDFs and JSON ground truths (DataLoaderService)
├── ai_agents/
│   ├── __init__.py
│   ├── ai_agent.py              # Abstract interface (AIAgent) for AI actions
│   ├── gemini_agent.py          # Concrete implementation of AIAgent using Google GenAI
│   ├── ollama_agent.py          # Concrete implementation of AIAgent using Ollama
│   └── openai_agent.py          # Concrete implementation of AIAgent using OpenAI Structured Outputs
├── data/
│   ├── documents/               # Folder containing PDF documents to process
│   ├── ground_truth.json        # Centralized JSON containing ground truths mapped by document ID
│   └── prompt_history.json      # Generated history of prompts per epoch
├── main.py                      # Main orchestration loop (run_prompt_gradient_descent)
├── requirements.txt             # Project external dependencies
└── .env                         # Environment variables (API Keys and parameters)
```

---

## ⚙️ How it Works (Prompt Optimization Loop)

For each iteration (up to `max_iterations`):
1. **Initial Seed**: Starts with a single default extraction prompt.
2. **Mini-Batch Extraction & Evaluation**: The IDs are processed in batches (configured by `batch_size`). For every PDF document:
   - Extracts structured rules (`ExtractedRules`) using the *current* system prompt.
   - Evaluates the extracted rules against its match in the central `ground_truth.json` to produce an individual error score (`0.0` to `1.0`) and qualitative feedback.
3. **Metrics Aggregation & History**:
   - Calculates the **average error score** across all evaluated PDFs in the epoch.
   - Combines feedback from all documents where errors were found.
   - Saves checkpoint history to `data/prompt_history.json`.
4. **Convergence Check**: Stops if the average error score meets the threshold configured in `settings.optimization_threshold`.
5. **Optimization (Gradient Step)**: Feeds the current system prompt, the average error score, and the combined feedback to the Prompt Expert Optimizer, which generates an updated, improved prompt.
6. **Iteration**: Repeats with the new prompt.

---

## 🚀 Getting Started

Follow these steps to set up and run the project locally on your machine.

### 1. Prerequisites

Make sure you have Python installed (version 3.10 or higher is recommended).
*If you plan to use Ollama, ensure you have [Ollama](https://ollama.com/) installed and running locally.*

### 2. Set Up the Environment Variables

Create a file named `.env` in the root directory of the project and add your API keys and configuration settings:

```env
GEMINI_API_KEY="your-gemini-api-key"
OPENAI_API_KEY="your-openai-api-key"
OLLAMA_HOST="http://localhost:11434"
OPTIMIZATION_THRESHOLD=0.05
MAX_ITERATIONS=5
BATCH_SIZE=5
```

### 3. Create a Virtual Environment

Open your terminal in the project root directory and run:

```bash
python3 -m venv .venv
```

### 4. Activate the Virtual Environment

* **Linux / macOS**: `source .venv/bin/activate`
* **Windows (Command Prompt)**: `.venv\Scripts\activate.bat`
* **Windows (PowerShell)**: `.venv\Scripts\Activate.ps1`

### 5. Install Dependencies

Install the required external libraries:

```bash
pip install -r requirements.txt
```

---

## 📂 Expected Input Format

To optimize prompts for your PDFs, organize your files as follows:

1. **PDFs Folder (`data/documents`)**: A folder containing your PDF files (e.g. `1.pdf`, `2.pdf`). The names should reflect their IDs.
2. **Ground Truth File (`data/ground_truth.json`)**: A single JSON file mapping the document IDs to their expected outputs.

The JSON ground truth must follow the structure:
```json
{
  "1": {
    "documents_needed": ["Identity Document", "Proof of Address"],
    "information_needed": ["Full Name", "Address details"]
  },
  "2": {
    "documents_needed": ["Passport"],
    "information_needed": ["Date of Birth"]
  }
}
```

---

## 🏃 Running the Pipeline

You can run the script using the python virtual environment. You can pass optional flags for logging and limiting the number of files:

```bash
python main.py --log --max-files 10
```

To integrate it into your code, instantiate the desired agent and service and invoke the descent loop:

```python
from ai_agents.ollama_agent import OllamaAgent # Or OpenAIAgent / GeminiAgent
from services.data_loaders_service import DataLoaderService
from main import run_prompt_gradient_descent

# Initialize components
agent = OllamaAgent()
loader = DataLoaderService()

# Run the optimization loop
optimal_prompt = run_prompt_gradient_descent(
    agent=agent,
    loader=loader,
    enable_logging=True
)

# Print the single global optimal prompt found
print(f"Optimal global prompt: {optimal_prompt}")
```
