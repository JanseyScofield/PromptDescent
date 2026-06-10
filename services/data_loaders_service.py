import json
import PyPDF2
from typing import List, Dict

class DataLoaderService:
    def read_pdfs(self, pdf_paths: List[str]) -> Dict[str, str]:
        pdf_texts = {}
        for path in pdf_paths:
            try:
                combined_text = ""
                with open(path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            combined_text += text + "\n"
                pdf_texts[path] = combined_text
            except Exception as e:
                print(f"Error reading {path}: {e}")
        return pdf_texts

    def load_ground_truth(self, json_path: str) -> Dict:
        with open(json_path, 'r') as file:
            return json.load(file)
