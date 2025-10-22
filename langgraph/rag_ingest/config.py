from dataclasses import dataclass


@dataclass
class IngestConfig:
    input_dir: str = ".rag_ingest/data/pdfs"
    chroma_dir: str = "./.chroma"
    collection: str = "innorules"
    model_name: str = "BAAI/bge-m3"
    device: str = "cpu"
    chunk_size: int = 1024
    chunk_overlap: int = 128
    batch_size: int = 8


# Semantic Chunking 설정
@dataclass
class ChunkConfig:
    model_name: str = "BAAI/bge-m3"
    device: str = "cpu"
    similarity_threshold: float = 0.75  # 유사도 임계값 (0.7~0.85 권장)
    min_sentences: int = 2  # 청크 최소 문장 수
    max_sentences: int = 20  # 청크 최대 문장 수
    min_tokens: int = 100  # 청크 최소 토큰 수
    max_tokens: int = 1024  # 청크 최대 토큰 수
    batch_size: int = 32  # 임베딩 배치 크기
