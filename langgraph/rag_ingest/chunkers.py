from typing import List, Optional
from dataclasses import dataclass
import logging
import numpy as np
import re
from sentence_transformers import SentenceTransformer
try:
    import tiktoken
    _enc = tiktoken.get_encoding("cl100k_base")
    TIKTOKEN_AVAILABLE = True
except ImportError:
    _enc = None
    TIKTOKEN_AVAILABLE = False

from .config import ChunkConfig


logger = logging.getLogger(__name__)


@dataclass
class ChunkWithPage:
    """페이지 정보를 포함한 청크"""
    text: str
    start_page: int
    end_page: int

    @property
    def page_str(self) -> str:
        """페이지 문자열 표현 (예: "5" or "5-6")"""
        if self.start_page == self.end_page:
            return str(self.start_page)
        return f"{self.start_page}-{self.end_page}"


class SemanticChunker:
    """
    BERT 기반 Semantic Chunking

    핵심 로직:
    1. 텍스트를 문장 단위로 분할
    2. 문장을 BERT로 임베딩
    3. 연속 문장 간 코사인 유사도 계산
    4. 유사도 임계값 이하 지점에서 청크 분리
    """

    def __init__(self, config: ChunkConfig = None):
        self.config = config or ChunkConfig()
        self._model = None
        logger.info(f"SemanticChunker 초기화: {self.config.model_name}")

    @property
    def model(self) -> SentenceTransformer:
        """모델 지연 로딩 (싱글톤)"""
        if self._model is None:
            try:
                self._model = SentenceTransformer(
                    self.config.model_name,
                    device=self.config.device
                )
                logger.info(f"임베딩 모델 로드 완료: {self.config.model_name}")
            except Exception as e:
                logger.error(f"모델 로드 실패: {e}")
                raise
        return self._model

    def split_sentences(self, text: str) -> List[str]:
        """
        텍스트를 문장 단위로 분할

        한국어 고려한 정교한 분할:
        - kss 라이브러리 사용 권장 (설치 시)
        - fallback: 정규표현식 기반
        """
        try:
            # kss 사용 (한국어 문장 분리에 최적화)
            import kss
            sentences = kss.split_sentences(text)
            return [s.strip() for s in sentences if s.strip()]
        except ImportError:
            pass

        # fallback: 정규표현식
        # 한국어: . ! ? 다음 공백
        # 영어: . ! ? 다음 대문자 또는 공백
        pattern = r'(?<=[.!?])\s+(?=[A-Z가-힣])|(?<=[.!?])\s*\n'
        sentences = re.split(pattern, text)

        # 빈 문장 제거 및 정리
        sentences = [s.strip() for s in sentences if s.strip()]

        # 너무 짧은 문장은 다음 문장과 병합
        merged = []
        temp = ""
        for s in sentences:
            if len(temp) < 20:  # 최소 20자
                temp += " " + s if temp else s
            else:
                if temp:
                    merged.append(temp)
                temp = s
        if temp:
            merged.append(temp)

        return merged

    def count_tokens(self, text: str) -> int:
        """토큰 수 계산"""
        if TIKTOKEN_AVAILABLE and _enc:
            return len(_enc.encode(text))
        # fallback: 문자 수 / 4 (대략적 추정)
        return len(text) // 4

    def compute_embeddings(self, sentences: List[str]) -> np.ndarray:
        """
        문장 리스트를 배치로 임베딩

        성능 최적화:
        - 배치 처리로 GPU 활용 극대화
        - normalize=True로 코사인 유사도 계산 단순화
        """
        try:
            embeddings = self.model.encode(
                sentences,
                batch_size=self.config.batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,  # L2 정규화 (코사인 유사도용)
                convert_to_numpy=True
            )
            return embeddings
        except Exception as e:
            logger.error(f"임베딩 계산 실패: {e}")
            raise

    def compute_similarities(self, embeddings: np.ndarray) -> List[float]:
        """
        연속된 문장 쌍의 코사인 유사도 계산

        최적화:
        - 정규화된 벡터는 내적 = 코사인 유사도
        - np.einsum으로 배치 계산
        """
        if len(embeddings) < 2:
            return []

        # 정규화된 벡터의 내적 = 코사인 유사도
        # similarities[i] = embeddings[i] · embeddings[i+1]
        similarities = np.einsum('ij,ij->i', embeddings[:-1], embeddings[1:])
        return similarities.tolist()

    def find_boundaries(
        self,
        sentences: List[str],
        similarities: List[float]
    ) -> List[int]:
        """
        청크 경계 인덱스 탐지

        전략:
        1. 유사도 < threshold인 지점을 후보로
        2. 최소/최대 문장 수 제약 적용
        3. 토큰 수 제약 추가 검증
        """
        boundaries = [0]  # 첫 청크 시작
        current_chunk_sentences = []
        current_chunk_tokens = 0

        for i, (sentence, sim) in enumerate(zip(sentences, similarities + [0.0])):
            sentence_tokens = self.count_tokens(sentence)
            current_chunk_sentences.append(sentence)
            current_chunk_tokens += sentence_tokens

            # 경계 조건 체크
            is_low_similarity = i < len(similarities) and similarities[i] < self.config.similarity_threshold
            exceeds_max_sentences = len(current_chunk_sentences) >= self.config.max_sentences
            exceeds_max_tokens = current_chunk_tokens >= self.config.max_tokens
            meets_min_sentences = len(current_chunk_sentences) >= self.config.min_sentences
            meets_min_tokens = current_chunk_tokens >= self.config.min_tokens

            # 경계 결정
            should_split = (
                (is_low_similarity or exceeds_max_sentences or exceeds_max_tokens) and
                meets_min_sentences and
                meets_min_tokens
            )

            if should_split:
                boundaries.append(i + 1)
                current_chunk_sentences = []
                current_chunk_tokens = 0

        # 마지막 경계 추가 (문장 끝)
        if boundaries[-1] != len(sentences):
            boundaries.append(len(sentences))

        return boundaries

    # def create_chunks(
    #     self,
    #     sentences: List[str],
    #     boundaries: List[int]
    # ) -> List[str]:
    #     """경계 인덱스를 기반으로 청크 생성"""
    #     chunks = []
    #     for i in range(len(boundaries) - 1):
    #         start = boundaries[i]
    #         end = boundaries[i + 1]
    #         chunk_sentences = sentences[start:end]
    #         chunk_text = " ".join(chunk_sentences)
    #         chunks.append(chunk_text.strip())

    #     return chunks

    def create_chunks_with_pages(
        self,
        sentences: List[str],
        sentence_pages: List[int],
        boundaries: List[int]
    ) -> List[ChunkWithPage]:
        """
        경계 인덱스 기반으로 청크 생성 (페이지 정보 포함)

        Args:
            sentences: 문장 리스트
            sentence_pages: 각 문장이 속한 페이지 번호 (sentences와 1:1 대응)
            boundaries: 청크 경계 인덱스

        Returns:
            ChunkWithPage 리스트
        """
        chunks = []
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]

            # 문장 슬라이싱
            chunk_sentences = sentences[start:end]
            chunk_text = " ".join(chunk_sentences)

            # 페이지 슬라이싱으로 범위 계산
            chunk_pages = sentence_pages[start:end]
            start_page = chunk_pages[0]
            end_page = chunk_pages[-1]

            chunks.append(ChunkWithPage(
                text=chunk_text.strip(),
                start_page=start_page,
                end_page=end_page
            ))

        return chunks

    def chunk(self, page_texts: List[str]) -> List[ChunkWithPage]:
        """
        메인 청킹 함수

        전체 파이프라인:
        1. 전체 문장 분할 + 페이지 매핑
        2. 임베딩 계산
        3. 유사도 계산
        4. 경계 탐지
        5. 청크 생성
        """
        if not page_texts:
            return []

        # 1. 전체 문장 분할, 페이지 매핑
        all_sentences = []
        sentence_pages = []

        for page_idx, page_text in enumerate(page_texts):
            page_sentences = self.split_sentences(page_text)
            all_sentences.extend(page_sentences)
            # 각 문장에 페이지 번호 부여
            sentence_pages.extend([page_idx + 1] * len(page_sentences))

        if not all_sentences:
            return []

        if len(all_sentences) == 1:
            return [ChunkWithPage(
                text=all_sentences[0],
                start_page=sentence_pages[0],
                end_page=sentence_pages[0]
            )]

        logger.debug(f"전체 {len(all_sentences)}개 문장, {len(page_texts)}개 페이지")

        # 2. 임베딩 계산
        try:
            embeddings = self.compute_embeddings(all_sentences)
        except Exception as e:
            logger.warning(f"임베딩 실패, 전체를 하나의 청크로: {e}")
            return [ChunkWithPage(
                text=" ".join(all_sentences),
                start_page=sentence_pages[0],
                end_page=sentence_pages[-1]
            )]

        # 3. 유사도 계산
        similarities = self.compute_similarities(embeddings)
        logger.debug(f"평균 유사도: {np.mean(similarities):.3f}")

        # 4. 경계 탐지
        boundaries = self.find_boundaries(all_sentences, similarities)
        logger.debug(f"청크 경계: {boundaries}")

        # 5. 청크 생성
        chunks = self.create_chunks_with_pages(all_sentences, sentence_pages, boundaries)

        logger.info(f"청킹 완료: {len(all_sentences)}개 문장 → {len(chunks)}개 청크")

        # 품질 검증
        for i, chunk_obj in enumerate(chunks):
            tokens = self.count_tokens(chunk_obj.text)
            if tokens < self.config.min_tokens:
                logger.warning(f"청크 {i} 토큰 수 부족: {tokens} < {self.config.min_tokens}")
            if tokens > self.config.max_tokens:
                logger.warning(f"청크 {i} 토큰 수 초과: {tokens} > {self.config.max_tokens}")

        return chunks


# 전역 싱글톤 인스턴스
_chunker_instance: Optional[SemanticChunker] = None


def get_semantic_chunker(config: ChunkConfig = None) -> SemanticChunker:
    """싱글톤 SemanticChunker 인스턴스 반환"""
    global _chunker_instance
    if _chunker_instance is None:
        _chunker_instance = SemanticChunker(config)
    return _chunker_instance


def chunk_text(
    text: str
) -> List[ChunkWithPage]:
    """
    통합 청킹 인터페이스

    Args:
        text: 입력 텍스트

    Returns:
        청크 리스트
    """
    config = ChunkConfig()
    chunker = get_semantic_chunker(config)

    try:
        return chunker.chunk(text)
    except Exception as e:
        logger.error(f"Semantic chunking 실패, fallback 사용: {e}")
        return _simple_chunk(text, config.max_tokens)


def _simple_chunk(text: str, chunk_size: int) -> List[str]:
    """Fallback: 단순 토큰 기반 분할"""
    if TIKTOKEN_AVAILABLE and _enc:
        tokens = _enc.encode(text)
        chunks = []
        for i in range(0, len(tokens), chunk_size):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = _enc.decode(chunk_tokens)
            chunks.append(chunk_text)
        return chunks
    else:
        # 최후 fallback: 문자 기반
        chunks = []
        char_size = chunk_size * 4
        for i in range(0, len(text), char_size):
            chunks.append(text[i:i + char_size])
        return chunks
