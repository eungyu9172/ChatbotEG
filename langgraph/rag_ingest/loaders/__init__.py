from typing import List
from .pdf_loader import load_pdf
from .txt_loader import load_txt


def load_document(filepath: str) -> List[str]:
    """
    파일 확장자에 따라 적절한 로더 선택
    반환: 페이지 단위 텍스트 리스트
    """
    ext = filepath.lower().rsplit(".", 1)[-1]

    if ext == "pdf":
        return load_pdf(filepath)
    elif ext == "txt":
        return load_txt(filepath)
    else:
        raise ValueError(f"지원하지 않는 파일 형식: {ext}")
