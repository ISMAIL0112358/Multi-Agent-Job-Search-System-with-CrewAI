import os
import re
import datetime
import logging
from typing import Optional
from backend.config import settings

logger = logging.getLogger(__name__)

_s3_client = None


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION
        )
    return _s3_client


def _get_user_dir(user_id: str, doc_type: str) -> str:
    """Get the directory path for a user's documents."""
    path = os.path.join(settings.DATA_DIR, "users", user_id, doc_type)
    os.makedirs(path, exist_ok=True)
    return path


def save_resume(user_id: str, filename: str, file_bytes: bytes) -> str:
    """Save a resume PDF to the user's resume directory. Returns the filepath or S3 key."""
    # Sanitize filename
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", filename)

    if settings.STORAGE_PROVIDER == "s3":
        try:
            s3 = _get_s3_client()
            s3_key = f"users/{user_id}/resumes/{safe_name}"
            s3.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=s3_key,
                Body=file_bytes,
                ContentType="application/pdf"
            )
            return s3_key
        except Exception as e:
            logger.error(f"Failed to upload user resume to S3: {e}")
            raise

    directory = _get_user_dir(user_id, "resumes")
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
    """Save a candidate resume PDF to the candidates directory. Returns the filepath or S3 key."""
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", filename)

    if settings.STORAGE_PROVIDER == "s3":
        try:
            s3 = _get_s3_client()
            s3_key = f"candidates/{candidate_id}/{safe_name}"
            s3.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=s3_key,
                Body=file_bytes,
                ContentType="application/pdf"
            )
            return s3_key
        except Exception as e:
            logger.error(f"Failed to upload candidate resume to S3: {e}")
            raise

    directory = os.path.join(settings.DATA_DIR, "candidates", candidate_id)
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, safe_name)
    with open(filepath, "wb") as f:
        f.write(file_bytes)
    return filepath


def generate_candidate_resume_download_url(candidate_id: str, filename: str) -> Optional[str]:
    """Generate a presigned S3 URL for resume download if using S3 storage."""
    if settings.STORAGE_PROVIDER != "s3":
        return None

    safe_name = re.sub(r'[\\/*?:"<>|]', "_", filename)
    s3_key = f"candidates/{candidate_id}/{safe_name}"

    try:
        s3 = _get_s3_client()
        url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": s3_key,
                "ResponseContentDisposition": f'attachment; filename="{filename}"'
            },
            ExpiresIn=900  # 15 minutes
        )
        return url
    except Exception as e:
        logger.error(f"Failed to generate presigned S3 URL for {s3_key}: {e}")
        return None

