def load_txt(filepath: str) -> list:
    """
    TXT 파일 전체를 하나의 페이지로 로드

    반환: [전체 텍스트] (길이 1인 리스트)
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 전체를 하나의 페이지로 반환
    return [content.strip()]
