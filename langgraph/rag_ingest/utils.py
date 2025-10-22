from typing import List
from datetime import datetime
import hashlib
import os


def iter_document_paths(root: str, extensions: List[str] = None):
    """
    지정된 확장자의 파일 경로 순회
    기본값: PDF, TXT
    """
    if extensions is None:
        extensions = [".pdf", ".txt"]

    extensions = [ext.lower() for ext in extensions]

    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if any(f.lower().endswith(ext) for ext in extensions):
                yield os.path.join(dirpath, f)


def get_file_type(filepath: str) -> str:
    """
    파일 확장자로부터 source_type 추출
    .pdf -> "pdf"
    .txt -> "txt"
    """
    ext = filepath.lower().rsplit(".", 1)[-1]
    return ext if ext in ["pdf", "txt"] else "unknown"


def content_hash(text: str) -> str:
    """텍스트 내용의 SHA256 해시 (앞 16자)"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def filename_hash(filename: str) -> str:
    """
    파일명의 SHA256 해시 (앞 16자)
    동일 파일명 = 동일 해시 = 동일 document_id
    """
    return hashlib.sha256(filename.encode("utf-8")).hexdigest()[:16]


def generate_document_id(filepath: str) -> str:
    """
    파일명 해시를 document_id로 사용
    형식: doc_{hash}
    예: doc_9a3f5c1d2e4b6789
    """
    filename = os.path.basename(filepath)
    hash_value = filename_hash(filename)
    return f"doc_{hash_value}"


def extract_title(filepath: str) -> str:
    """파일명을 title로 사용 (확장자 제외)"""
    filename = os.path.basename(filepath)
    return filename.rsplit(".", 1)[0]


def generate_chunk_id(document_id: str, page_str: str, chunk_idx: int, chunk_hash: str) -> str:
    """결정적 chunk_id 생성"""
    page_part = page_str.replace("-", "_")
    return f"{document_id}#p{page_part}-c{chunk_idx:03d}-h{chunk_hash[:8]}"


def now_iso() -> str:
    return datetime.now().isoformat()
