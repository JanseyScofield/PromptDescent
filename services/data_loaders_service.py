import json
import PyPDF2
from typing import List, Dict

class DataLoaderService:
    def read_pdfs(self, pdf_paths: List[str]) -> str:
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

    def load_ground_truth(self, json_path: str) -> Dict:
        with open(json_path, 'r') as file:
            return json.load(file)
