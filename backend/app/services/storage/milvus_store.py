"""
Milvus RAG 저장소
- OCR 블록을 임베딩해서 Milvus에 저장
- quoted_text로 유사 블록 검색 → bbox 반환
"""
from __future__ import annotations

import os
import json
from typing import TYPE_CHECKING

from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

if TYPE_CHECKING:
    from app.services.review.engine import ParsedDocument

MILVUS_HOST = os.getenv("MILVUS_HOST", "milvus")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
COLLECTION_NAME = "clms_ocr_blocks"
EMBEDDING_DIM = 1024  # bge-m3

_embedding_model = None
_collection = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("BAAI/bge-m3")
        print("[Milvus] 임베딩 모델 로드 완료")
    return _embedding_model


def _get_collection() -> Collection:
    global _collection
    if _collection is not None:
        return _collection

    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)

    if not utility.has_collection(COLLECTION_NAME):
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="document_id", dtype=DataType.INT64),
            FieldSchema(name="block_id", dtype=DataType.INT64),
            FieldSchema(name="page_no", dtype=DataType.INT64),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="bbox", dtype=DataType.VARCHAR, max_length=200),  # JSON string
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
        ]
        schema = CollectionSchema(fields=fields, description="OCR blocks for RAG")
        _collection = Collection(name=COLLECTION_NAME, schema=schema)
        _collection.create_index(
            field_name="embedding",
            index_params={"metric_type": "COSINE", "index_type": "IVF_FLAT", "params": {"nlist": 128}},
        )
        print(f"[Milvus] 컬렉션 생성: {COLLECTION_NAME}")
    else:
        _collection = Collection(name=COLLECTION_NAME)
        _collection.load()
        print(f"[Milvus] 컬렉션 로드: {COLLECTION_NAME}")

    return _collection


def store_blocks(parsed_doc: "ParsedDocument") -> bool:
    """OCR 블록을 Milvus에 임베딩해서 저장"""
    try:
        model = _get_embedding_model()
        collection = _get_collection()

        # 기존 document_id 데이터 삭제
        collection.delete(expr=f"document_id == {parsed_doc.document_id}")

        blocks_with_bbox = [b for b in parsed_doc.blocks if any(v > 0 for v in b.bbox)]
        if not blocks_with_bbox:
            print(f"[Milvus] document_id={parsed_doc.document_id} bbox 있는 블록 없음")
            return False

        texts = [b.text for b in blocks_with_bbox]
        embeddings = model.encode(texts, normalize_embeddings=True).tolist()

        data = [
            [parsed_doc.document_id] * len(blocks_with_bbox),  # document_id
            [b.block_id for b in blocks_with_bbox],             # block_id
            [b.page_no for b in blocks_with_bbox],              # page_no
            texts,                                               # text
            [json.dumps(b.bbox) for b in blocks_with_bbox],     # bbox
            embeddings,                                          # embedding
        ]
        collection.insert(data)
        collection.flush()
        print(f"[Milvus] {len(blocks_with_bbox)}개 블록 저장 (doc_id={parsed_doc.document_id})")
        return True

    except Exception as e:
        print(f"[Milvus] 저장 실패: {e}")
        return False


def search_blocks(
    quoted_text: str,
    document_id: int,
    top_k: int = 3,
) -> list[dict]:
    """quoted_text와 유사한 블록 검색 → bbox 반환"""
    try:
        model = _get_embedding_model()
        collection = _get_collection()

        embedding = model.encode([quoted_text], normalize_embeddings=True).tolist()

        results = collection.search(
            data=embedding,
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"nprobe": 10}},
            limit=top_k,
            expr=f"document_id == {document_id}",
            output_fields=["block_id", "page_no", "text", "bbox"],
        )

        highlights = []
        for hit in results[0]:
            bbox = json.loads(hit.entity.get("bbox", "[0,0,0,0]"))
            if any(v > 0 for v in bbox):
                highlights.append({
                    "page_no":  hit.entity.get("page_no"),
                    "bbox":     bbox,
                    "block_id": hit.entity.get("block_id"),
                    "score":    hit.score,
                    "text":     hit.entity.get("text", "")[:50],
                })

        return highlights

    except Exception as e:
        print(f"[Milvus] 검색 실패: {e}")
        return []