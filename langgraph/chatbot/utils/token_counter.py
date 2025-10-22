try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken not available. Using approximate token counting.")


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """텍스트의 토큰 수를 계산합니다."""
    if TIKTOKEN_AVAILABLE:
        try:
            # OpenAI 모델별 정확한 토큰 계산
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception:
            # fallback to cl100k_base encoding
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
    else:
        # 간단한 추정: 평균적으로 한국어 1토큰 ≈ 0.75글자, 영어 1토큰 ≈ 4글자
        korean_chars = len([c for c in text if ord(c) > 127])
        english_chars = len(text) - korean_chars

        estimated_tokens = int(korean_chars / 0.75) + int(english_chars / 4)
        return max(estimated_tokens, len(text.split()))  # 최소값은 단어 수
