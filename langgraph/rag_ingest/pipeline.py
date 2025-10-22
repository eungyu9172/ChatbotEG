from tqdm import tqdm

from .config import IngestConfig
from .loaders import load_document
from .chunkers import chunk_text
from .store_chroma import ChromaStore
from .utils import (
    iter_document_paths,
    get_file_type,
    content_hash,
    now_iso,
    generate_document_id,
    extract_title,
    generate_chunk_id
)


def run_ingest(config: IngestConfig):
    store = ChromaStore(
        path=config.chroma_dir,
        collection=config.collection,
        embedding_model=config.model_name
    )
    print(f"임베딩 모델: {config.model_name}")

    # 1) 로드
    doc_paths = list(iter_document_paths(config.input_dir, extensions=[".pdf", ".txt"]))
    print(f"문서 파일: {len(doc_paths)}개")

    for path in tqdm(doc_paths, desc="Load Documents"):
        source_type = get_file_type(path)
        document_id = generate_document_id(path)
        title = extract_title(path)

        # 기존 버전 확인
        existing_version = store.get_latest_version(document_id)
        new_version = existing_version + 1

        # 생성/수정 시각 설정
        if existing_version == 0:
            created = now_iso()
            updated = created
            print(f"📄 신규: {title} ({source_type.upper()}, {document_id[:16]}...)")
        else:
            existing_created = store.get_created_time(document_id)
            created = existing_created if existing_created else now_iso()
            updated = now_iso()
            print(f"🔄 업데이트: {title} ({source_type.upper()}) v{existing_version} → v{new_version}")
            store.delete_document(document_id)

        # 문서 로드
        try:
            pages = load_document(path)
        except Exception as e:
            print(f"  ❌ 로드 실패: {e}")
            continue

        if not pages:
            print("  ⚠️  빈 문서")
            continue

        print(f"  📑 {len(pages)}개 페이지 로드")

        # Semantic Chunking
        try:
            chunks = chunk_text(pages)
        except Exception as e:
            print(f"  ❌ 청킹 실패: {e}")
            continue

        if not chunks:
            print("  ⚠️  유효한 청크 없음")
            continue

        print(f"  ✅ {len(chunks)}개 청크 생성")

        # 메타데이터 생성
        all_chunks_metadata = []
        all_chunk_ids = []
        all_chunk_texts = []

        total_chunk_count = len(chunks)

        # 메타데이터 생성
        for chunk_idx, chunk_obj in enumerate(chunks):
            chunk_hash = content_hash(chunk_obj.text)
            page_str = chunk_obj.page_str

            chunk_id = generate_chunk_id(
                document_id,
                page_str,
                chunk_idx,
                chunk_hash
            )

            metadata = {
                "document_id": document_id,
                "title": title,
                "chunk_id": chunk_id,
                "page_str": page_str,
                "chunk_idx": chunk_idx,
                "chunk_count": total_chunk_count,
                "length": len(chunk_obj.text),
                "hash": chunk_hash,
                "version": new_version,
                "embedding_model": config.model_name,
                "source_type": source_type,
                "created": created,
                "updated": updated
            }

            all_chunk_ids.append(chunk_id)
            all_chunk_texts.append(chunk_obj.text)
            all_chunks_metadata.append(metadata)

        # 배치 업서트
        batch_size = config.batch_size
        for i in tqdm(
            range(0, len(all_chunk_texts), batch_size),
            desc=f"Upsert {title}",
            leave=False
        ):
            sl = slice(i, i + batch_size)
            store.upsert(
                ids=all_chunk_ids[sl],
                texts=all_chunk_texts[sl],
                metadatas=all_chunks_metadata[sl]
            )

        print(f"✅ {title} v{new_version}: {len(all_chunk_texts)}개 청크 등록 ({source_type.upper()})")

    print(f"\n🎉 총 {len(doc_paths)}개 문서 처리 완료")
