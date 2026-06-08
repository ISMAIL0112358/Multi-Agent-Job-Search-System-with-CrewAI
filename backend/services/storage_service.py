import os
import re
import datetime

from backend.config import settings


def _get_user_dir(user_id: str, doc_type: str) -> str:
    """Get the directory path for a user's documents."""
    path = os.path.join(settings.DATA_DIR, "users", user_id, doc_type)
    os.makedirs(path, exist_ok=True)
    return path


def save_resume(user_id: str, filename: str, file_bytes: bytes) -> str:
    """Save a resume PDF to the user's resume directory. Returns the filepath."""
    directory = _get_user_dir(user_id, "resumes")
    # Sanitize filename
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", filename)
    filepath = os.path.join(directory, safe_name)
    with open(filepath, "wb") as f:
        f.write(file_bytes)
    return filepath


def save_cover_letter(user_id: str, job_title: str, content: str) -> str:
    """Save a generated cover letter to the user's cover_letters directory. Returns filepath."""
    directory = _get_user_dir(user_id, "cover_letters")
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", job_title)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_title}_{timestamp}.txt"
    filepath = os.path.join(directory, filename)
    with open(filepath, "w") as f:
        f.write(content)
    return filepath


def save_generated_resume(user_id: str, job_title: str, content: str) -> str:
    """Save a tailored resume to the user's resumes directory. Returns filepath."""
    directory = _get_user_dir(user_id, "resumes")
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", job_title)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tailored_{safe_title}_{timestamp}.txt"
    filepath = os.path.join(directory, filename)
    with open(filepath, "w") as f:
        f.write(content)
    return filepath


def get_user_documents(user_id: str, doc_type: str) -> list:
    """List all documents for a user of a given type (resumes or cover_letters)."""
    directory = _get_user_dir(user_id, doc_type)
    files = []
    for fname in sorted(os.listdir(directory), reverse=True):
        fpath = os.path.join(directory, fname)
        if os.path.isfile(fpath):
            files.append({
                "filename": fname,
                "filepath": fpath,
                "size": os.path.getsize(fpath),
                "modified": datetime.datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat(),
            })
    return files


def save_candidate_resume(candidate_id: str, filename: str, file_bytes: bytes) -> str:
    """Save a candidate resume PDF to the candidates directory. Returns the filepath."""
    directory = os.path.join(settings.DATA_DIR, "candidates", candidate_id)
    os.makedirs(directory, exist_ok=True)
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", filename)
    filepath = os.path.join(directory, safe_name)
    with open(filepath, "wb") as f:
        f.write(file_bytes)
    return filepath

