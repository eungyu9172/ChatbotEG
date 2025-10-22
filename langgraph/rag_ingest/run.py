import argparse
from rich import print
from .config import IngestConfig
from .pipeline import run_ingest


def main():
    parser = argparse.ArgumentParser("RAG Ingest")
    parser.add_argument("--input-dir", type=str, default="./rag_ingest/data", help="입력 디렉터리")
    parser.add_argument("--chroma-dir", type=str, default="./.chroma", help="ChromaDB 경로")
    parser.add_argument("--collection", type=str, default="innorules", help="컬렉션 이름")
    parser.add_argument("--model", type=str, default="BAAI/bge-m3", help="임베딩 모델")
    parser.add_argument("--chunk-size", type=int, default=1024, help="최대 청크 크기")
    parser.add_argument("--batch-size", type=int, default=8, help="배치 크기")
    parser.add_argument("--device", type=str, default="cpu", help="디바이스 (cpu/cuda)")
    args = parser.parse_args()

    config = IngestConfig(
        input_dir=args.input_dir,
        chroma_dir=args.chroma_dir,
        collection=args.collection,
        model_name=args.model,
        chunk_size=args.chunk_size,
        batch_size=args.batch_size,
        device=args.device
    )

    print("=" * 60)
    print("📚 문서 인제스트 시작")
    print("=" * 60)
    print(f"입력 디렉터리: {config.input_dir}")
    print(f"ChromaDB 경로: {config.chroma_dir}")
    print(f"컬렉션: {config.collection}")
    print(f"모델: {config.model_name}")
    print(f"청크 크기: {config.chunk_size}")
    print("=" * 60)

    run_ingest(config)

    print("\n✅ 인제스트 완료!")


if __name__ == "__main__":
    main()
