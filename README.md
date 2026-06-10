# Prompt Descent Optimization Pipeline

An automated prompt optimization pipeline inspired by gradient descent. This project refines a **single** global System Prompt iteratively across a batch of multiple PDF documents to find the best prompt that satisfies all documents simultaneously. It evaluates the outputs of all documents in each iteration against their individual Ground Truth JSON files, computing an average error score and combining feedback to guide the prompt optimizer.

---

## 🏗️ Architecture & Project Structure

The project has been refactored into a modular, clean, and decoupled architecture:

```text
prompt-descent/
├── config/
│   ├── __init__.py
│   └── app_settings.py          # Handles app configurations (Pydantic Settings) and OpenAI client initialization
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
│   └── openai_agent.py          # Concrete implementation of AIAgent using OpenAI Structured Outputs
├── main.py                      # Main orchestration loop (run_prompt_gradient_descent)
├── requirements.txt             # Project external dependencies
└── .env                         # Environment variables (API Key and parameters)
```

---

## ⚙️ How it Works (Prompt Optimization Loop)

For each iteration (up to `max_iterations`):
1. **Initial Seed**: Starts with a single default extraction prompt.
2. **Batch Extraction & Evaluation**: For every PDF document:
   - Extracts structured rules (`ExtractedRules`) using the *current* system prompt.
   - Evaluates the extracted rules against the matching Ground Truth JSON file to produce an individual error score (`0.0` to `1.0`) and qualitative feedback.
3. **Metrics Aggregation**:
   - Calculates the **average error score** across all PDFs.
   - Combines feedback from all documents where errors were found.
4. **Convergence Check**: Stops if the average error score meets the threshold configured in `settings.optimization_threshold`.
5. **Optimization (Gradient Step)**: Feeds the current system prompt, the average error score, and the combined feedback to the Prompt Expert Optimizer, which generates an updated, improved prompt.
6. **Iteration**: Repeats with the new prompt.

---

## 🚀 Getting Started

Follow these steps to set up and run the project locally on your machine.

### 1. Prerequisites

Make sure you have Python installed (version 3.10 or higher is recommended).

### 2. Set Up the Environment Variables

Create a file named `.env` in the root directory of the project and add your OpenAI API key and configuration settings:

```env
OPENAI_API_KEY="your-api-key-here"
OPTIMIZATION_THRESHOLD=0.05
MAX_ITERATIONS=5
```

### 3. Create a Virtual Environment

Open your terminal in the project root directory and run:

```bash
# Create the virtual environment
python3 -m venv .venv
```

### 4. Activate the Virtual Environment

Activate the environment depending on your operating system:

* **Linux / macOS**:
  ```bash
  source .venv/bin/activate
  ```
* **Windows (Command Prompt)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
* **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

Once activated, your terminal prompt will show `(.venv)`.

### 5. Install Dependencies

Install the required external libraries:

```bash
pip install -r requirements.txt
```

---

## 📂 Expected Input Format

To optimize prompts for your PDFs, organize your files as follows:

1. **PDFs Folder**: A folder containing your PDF files (e.g. `documents/rules_1.pdf`, `documents/rules_2.pdf`).
2. **Ground Truth Folder**: A folder containing `.json` files. The filename must match the PDF name (e.g. `data/ground_truths/rules_1.json`, `data/ground_truths/rules_2.json`).

The JSON ground truth files must follow the extraction structure:
```json
{
  "documents_needed": [
    "Identity Document",
    "Proof of Address"
  ],
  "information_needed": [
    "Full Name",
    "Address details"
  ]
}
```

---

## 🏃 Running the Pipeline

You can run the script using the python virtual environment:

```bash
python main.py
```

To integrate it into your code, instantiate the agent and service and invoke the descent loop:

```python
from ai_agents.openai_agent import OpenAIAgent
from services.data_loaders_service import DataLoaderService
from main import run_prompt_gradient_descent

# Initialize components
agent = OpenAIAgent()
loader = DataLoaderService()

# Run the optimization loop
optimal_prompt = run_prompt_gradient_descent(
    agent=agent,
    loader=loader,
    pdf_paths=["documents/rules_1.pdf", "documents/rules_2.pdf"],
    ground_truth_dir="data/ground_truths"
)

# Print the single global optimal prompt found
print(f"Optimal global prompt: {optimal_prompt}")
```
