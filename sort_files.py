import os
import re
import shutil
from PyPDF2 import PdfReader
from docx import Document

# --- CONFIGURATION ---

DOWNLOADS_DIR = r"C:\Users\YourName\Downloads"   # Change to your Downloads path
DEST_BASE = r"C:\Users\YourName\Documents\SortedDocs"

# Define keyword-based folder rules
CATEGORY_RULES = {
    "Finance": ["invoice", "payment", "receipt", "tax", "bill"],
    "Engineering": ["spec", "technical", "design", "blueprint", "circuit"],
    "HR": ["resume", "cv", "employee", "salary", "hiring"],
    "Legal": ["contract", "agreement", "nda", "policy"],
    "Reports": ["report", "analysis", "summary", "review"]
}

# --- FILE HANDLERS ---

def extract_text_from_pdf(filepath):
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages[:5]:  # limit to first few pages for speed
            text += page.extract_text() or ""
        return text.lower()
    except Exception as e:
        print(f"PDF read error ({filepath}): {e}")
        return ""

def extract_text_from_docx(filepath):
    try:
        doc = Document(filepath)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.lower()
    except Exception as e:
        print(f"DOCX read error ({filepath}): {e}")
        return ""

def get_file_category(text):
    for category, keywords in CATEGORY_RULES.items():
        for word in keywords:
            if re.search(rf"\b{word}\b", text):
                return category
    return "Unsorted"

def move_file(src_path, category):
    dest_dir = os.path.join(DEST_BASE, category)
    os.makedirs(dest_dir, exist_ok=True)
    shutil.move(src_path, os.path.join(dest_dir, os.path.basename(src_path)))
    print(f"Moved → {category}: {os.path.basename(src_path)}")

# --- MAIN LOGIC ---

def sort_files():
    for filename in os.listdir(DOWNLOADS_DIR):
        filepath = os.path.join(DOWNLOADS_DIR, filename)
        if not os.path.isfile(filepath):
            continue

        ext = os.path.splitext(filename)[1].lower()
        text = ""

        if ext == ".pdf":
            text = extract_text_from_pdf(filepath)
        elif ext == ".docx":
            text = extract_text_from_docx(filepath)
        else:
            continue  # skip non-doc files

        category = get_file_category(text)
        move_file(filepath, category)

if __name__ == "__main__":
    sort_files()
