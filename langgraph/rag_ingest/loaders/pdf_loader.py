from typing import List


def normalize_text(text: str) -> str:
    """텍스트 정규화"""
    return " ".join(text.replace("\u00ad", "").split())


def load_pdf(filepath: str) -> List[str]:
    """PDF 파일을 페이지 단위로 로드"""
    pages = []
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(filepath)
        for page in doc:
            pages.append(normalize_text(page.get_text("text")))
        doc.close()
        return pages
    except Exception:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        for page in reader.pages:
            pages.append(normalize_text(page.extract_text() or ""))
        return pages
