import re
from typing import List


def extract_pronouns_and_references(text: str) -> List[str]:
    """
    입력 쿼리에서 '인칭 대명사·지시어'를 추출한다.
    ──────────────────────────────────────────────
    Args
        text (str): 사용자가 입력한 원문 쿼리
    Returns
        List[str]: 발견된 대명사·지시어(소문자) 목록
    """

    # 1. 탐지 대상 토큰(확장 가능)
    #   - 영어·한국어 혼재 환경을 고려해 두 언어를 우선 포함
    pronouns_en = [
        "i", "me", "my", "mine", "myself",
        "you", "your", "yours", "yourself",
        "he", "him", "his", "himself",
        "she", "her", "hers", "herself",
        "it", "its", "itself",
        "we", "us", "our", "ours", "ourselves",
        "they", "them", "their", "theirs", "themselves"
    ]
    pronouns_ko = [
        "나", "저", "우리", "저희",
        "그", "그녀", "그들", "그것",
        "너", "당신", "너희", "당신들"
    ]
    demonstratives_en = ["this", "that", "these", "those"]
    demonstratives_ko = ["이것", "저것", "그것", "이", "그", "저"]

    vocab = pronouns_en + pronouns_ko + demonstratives_en + demonstratives_ko

    # 2. 정규식 빌드 (단어 경계 사용, 대소문자 무시)
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, vocab)) + r")\b", re.IGNORECASE)

    # 3. 매칭
    matches = pattern.findall(text)

    # 4️. 소문자·중복 제거 정리
    return sorted(set(m.lower() for m in matches))
