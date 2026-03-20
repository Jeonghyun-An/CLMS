"""
RAG 서비스 (Vector + Graph)

실제 연동 포인트:
- retrieve_context()   → pymilvus 교체
- retrieve_graph_context() → neo4j 드라이버 교체
- 임베딩               → settings.VLLM_BASE_URL 의 /v1/embeddings 엔드포인트

PoC: 키워드 기반 mock으로 동작, 인터페이스는 실제와 동일하게 유지
"""

import re
from dataclasses import dataclass
from typing import Optional

from app.data.knowledge_base import LEGAL_ARTICLES, ARTICLE_MAP, LegalArticle


@dataclass
class RetrievedChunk:
    article_id: str
    source: str
    article: str
    title: str
    content: str
    score: float
    retrieval_type: str   # "vector" | "graph" | "keyword_mock"


# ─── Mock Vector Store ───────────────────────────────────────────────────────

def _keyword_score(query: str, article: LegalArticle) -> float:
    """PoC: 키워드 오버랩 기반 유사도 (실제: Milvus cosine similarity)"""
    q = set(re.findall(r'[가-힣a-zA-Z0-9]+', query.lower()))
    corpus = (article["content"] + " " + " ".join(article["tags"])).lower()
    a = set(re.findall(r'[가-힣a-zA-Z0-9]+', corpus))
    return min(len(q & a) / len(q), 1.0) if q else 0.0


async def retrieve_context(
    query: str,
    category: Optional[str] = None,
    top_k: int = 3,
) -> list[RetrievedChunk]:
    """
    벡터 유사도 검색

    실제 구현:
        embedding = await httpx.post(f"{settings.VLLM_BASE_URL}/embeddings", ...)
        results = milvus_client.search(collection_name="legal_articles", ...)
    """
    candidates = [
        a for a in LEGAL_ARTICLES
        if category is None or a["category"] in (category, "contract")
    ]
    scored = sorted(
        [(a, _keyword_score(query, a)) for a in candidates],
        key=lambda x: x[1], reverse=True,
    )
    return [
        RetrievedChunk(
            article_id=a["id"], source=a["source"], article=a["article"],
            title=a["title"], content=a["content"],
            score=round(s, 3), retrieval_type="keyword_mock",
        )
        for a, s in scored[:top_k] if s > 0
    ]


# ─── Mock Graph Store ────────────────────────────────────────────────────────

# 조항 간 관계 그래프 (PoC 하드코딩)
# 실제: Neo4j (Article)-[:REFERENCES]->(Article)
ARTICLE_GRAPH: dict[str, list[str]] = {
    "lca_30_1":          ["lca_30_2", "internal_approval_1"],
    "lca_66_1":          ["lca_30_1"],
    "lca_62":            ["lca_30_1", "lca_66_1"],
    "internal_approval_1": ["internal_approval_2", "lca_30_1"],
    "internal_approval_2": ["internal_approval_1"],
    "cost_labor_1":      [],
}


async def retrieve_graph_context(
    seed_article_ids: list[str],
    depth: int = 1,
) -> list[RetrievedChunk]:
    """
    Graph RAG: 시드 조항에서 관련 조항 네트워크 탐색

    실제 구현:
        neo4j.run(
            "MATCH (a:Article {id: $seed})-[:REFERENCES*1..2]->(b) RETURN b",
            seed=seed_id
        )
    """
    visited = set(seed_article_ids)
    to_visit = list(seed_article_ids)
    chunks: list[RetrievedChunk] = []

    for _ in range(depth):
        next_visit: list[str] = []
        for aid in to_visit:
            for nid in ARTICLE_GRAPH.get(aid, []):
                if nid not in visited:
                    visited.add(nid)
                    next_visit.append(nid)
                    art = ARTICLE_MAP.get(nid)
                    if art:
                        chunks.append(RetrievedChunk(
                            article_id=nid, source=art["source"],
                            article=art["article"], title=art["title"],
                            content=art["content"], score=0.8,
                            retrieval_type="graph",
                        ))
        to_visit = next_visit

    return chunks
