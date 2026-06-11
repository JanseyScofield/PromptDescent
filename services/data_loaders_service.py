import json
import os
import PyPDF2
from typing import List, Dict

class DataLoaderService:
    def map_pdfs_by_id(self, pdfs_directory: str) -> Dict[str, str]:
        """
        Scans a directory for PDF files and maps their ID (numeric prefix before underscore) 
        to their full file path.
        Example: '123_rules.pdf' -> ID '123'
        """
        mapping = {}
        if not os.path.exists(pdfs_directory):
            print(f"Directory not found: {pdfs_directory}")
            return mapping

        for filename in os.listdir(pdfs_directory):
            if filename.lower().endswith(".pdf"):
                # Extract ID: everything before the first underscore, or the filename itself
                raw_id = filename.split('_')[0] if '_' in filename else os.path.splitext(filename)[0]
                try:
                    # Normalize ID: remove leading zeros (e.g., "01" -> "1")
                    file_id = str(int(raw_id))
                except ValueError:
                    file_id = raw_id
                mapping[file_id] = os.path.join(pdfs_directory, filename)
        
        return mapping

    def read_pdf(self, pdf_path: str) -> str:
        """Reads a single PDF and returns its text."""
        try:
            combined_text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        combined_text += text + "\n"
            return combined_text
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
            return ""

    def read_pdfs(self, pdf_paths: List[str]) -> Dict[str, str]:
        pdf_texts = {}
        for path in pdf_paths:
            text = self.read_pdf(path)
            if text:
                pdf_texts[path] = text
        return pdf_texts

    def load_ground_truth(self, json_path: str) -> Dict:
        """Loads a single JSON file containing multiple ground truths indexed by ID."""
        with open(json_path, 'r') as file:
            data = json.load(file)
            return {str(item["id"]): item for item in data}
