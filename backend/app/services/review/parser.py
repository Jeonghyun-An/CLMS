"""
실제 파일 파서 — ZIP 포맷(jpeg+txt+manifest.json) 문서 처리
────────────────────────────────────────────────────────────
입력:  파일 경로 (입찰공고문.pdf / 입찰공고문_비정상.pdf)
출력:  ParsedDocument (기존 엔진과 동일 인터페이스)

파일 구조:
  manifest.json  → 페이지별 이미지/텍스트 경로 + 이미지 크기
  1.jpeg, 2.jpeg → 페이지 이미지 (PDF.js 뷰어에서 사용)
  1.txt, 2.txt   → OCR/텍스트 추출 결과
"""

from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from app.services.review.engine import ParsedBlock, ParsedDocument


# ──────────────────────────────────────────────
# 페이지 메타 (이미지 크기 포함 — 하이라이트 좌표 계산용)
# ──────────────────────────────────────────────

@dataclass
class PageMeta:
    page_no: int
    img_path: str          # ZIP 내부 경로 (예: "1.jpeg")
    width: int             # 이미지 원본 너비 (px)
    height: int            # 이미지 원본 높이 (px)
    text: str              # 전체 텍스트


@dataclass
class ParsedDocumentWithMeta:
    document_id: int
    file_path: str
    pages: list[PageMeta] = field(default_factory=list)

    @property
    def as_engine_doc(self) -> ParsedDocument:
        """룰 엔진용 ParsedDocument 로 변환 (줄 단위 블록)"""
        doc = ParsedDocument(document_id=self.document_id)
        block_id = 1
        for page in self.pages:
            lines = [l.strip() for l in page.text.splitlines() if l.strip()]
            for line in lines:
                # 간단한 bbox 추정 — 실제 좌표 없으므로 (0,0,0,0) 사용
                # 하이라이트는 manifest 이미지 크기 + 텍스트 검색으로 별도 처리
                doc.blocks.append(ParsedBlock(
                    block_id=block_id,
                    page_no=page.page_no,
                    text=line,
                    bbox=[0, 0, 0, 0],
                ))
                block_id += 1
        return doc


# ──────────────────────────────────────────────
# 파서
# ──────────────────────────────────────────────

def parse_zip_doc(file_path: str, document_id: int = 1) -> ParsedDocumentWithMeta:
    """ZIP 기반 문서 파일을 파싱하여 ParsedDocumentWithMeta 반환"""
    result = ParsedDocumentWithMeta(
        document_id=document_id,
        file_path=file_path,
    )
    with zipfile.ZipFile(file_path) as z:
        manifest = json.loads(z.read("manifest.json"))
        for p in manifest["pages"]:
            page_no = p["page_number"]
            img_path = p["image"]["path"]
            width    = p["image"]["dimensions"]["width"]
            height   = p["image"]["dimensions"]["height"]
            txt_path = p["text"]["path"]
            text     = z.read(txt_path).decode("utf-8", errors="ignore")

            result.pages.append(PageMeta(
                page_no=page_no,
                img_path=img_path,
                width=width,
                height=height,
                text=text,
            ))
    return result


def get_page_image_bytes(file_path: str, page_no: int) -> bytes | None:
    """특정 페이지 이미지 바이트 반환 (API에서 이미지 서빙용)"""
    with zipfile.ZipFile(file_path) as z:
        manifest = json.loads(z.read("manifest.json"))
        for p in manifest["pages"]:
            if p["page_number"] == page_no:
                return z.read(p["image"]["path"])
    return None


# ──────────────────────────────────────────────
# 텍스트 기반 좌표 추정
# (실제 OCR bbox 없을 때 — 줄 번호로 y 추정)
# ──────────────────────────────────────────────

def estimate_bbox_from_line(
    text: str,
    search_text: str,
    page_width: int,
    page_height: int,
) -> list[float] | None:
    """
    페이지 전체 텍스트에서 search_text가 있는 줄의
    대략적인 y 위치를 비율로 추정.
    반환: [x1_ratio, y1_ratio, x2_ratio, y2_ratio]
    """
    lines = text.splitlines()
    total = len(lines)
    if total == 0:
        return None

    for i, line in enumerate(lines):
        if search_text in line:
            y_ratio_top    = i / total
            y_ratio_bottom = (i + 1) / total
            # x는 텍스트 길이 비례로 추정 (왼쪽 여백 7%)
            x_start = 0.07
            x_end   = min(0.07 + len(line) / (page_width / 8), 0.95)
            return [x_start, y_ratio_top, x_end, y_ratio_bottom]
    return None


# ──────────────────────────────────────────────
# 실제 문서 기반 룰 체크 (정확도 향상 버전)
# ──────────────────────────────────────────────

def run_review_on_real_doc(
    file_path: str,
    document_id: int = 1,
) -> tuple[list[dict], ParsedDocumentWithMeta]:
    """
    실제 파일을 파싱하고 룰 엔진을 실행.
    반환: (이슈 목록 with 실제 좌표, ParsedDocumentWithMeta)
    """
    from app.services.review.engine import run_review, issues_to_api_response

    parsed = parse_zip_doc(file_path, document_id)
    engine_doc = parsed.as_engine_doc

    # 룰 엔진 실행
    raw_issues = run_review(engine_doc)
    issues = issues_to_api_response(raw_issues, document_id=document_id)

    # 각 이슈에 실제 페이지 이미지 좌표 보강
    for issue in issues:
        _enrich_highlights(issue, parsed)

    return issues, parsed


def _enrich_highlights(issue: dict, parsed: ParsedDocumentWithMeta):
    """
    이슈의 evidences 텍스트를 기반으로
    실제 페이지에서 bbox 비율 좌표를 찾아 highlights에 추가.
    """
    enriched = []

    # evidence 텍스트로 좌표 찾기
    for ev in issue.get("evidences", []):
        quoted = ev.get("quoted_text", "")
        page_no = ev.get("page_no", 1)
        if not quoted:
            continue

        page = next((p for p in parsed.pages if p.page_no == page_no), None)
        if not page:
            continue

        # 텍스트에서 줄 위치 추정
        search = quoted[:30].strip()  # 앞 30자로 검색
        bbox = estimate_bbox_from_line(
            page.text, search, page.width, page.height
        )
        if bbox:
            enriched.append({
                "page_no": page_no,
                "bbox_ratio": bbox,
                "block_id": ev.get("block_id"),
                "severity": issue["severity"],
                "rule_id": issue["rule_id"],
            })

    # evidences 없는 경우 (keyword_missing) — page 1 상단에 표시
    if not enriched and issue.get("category") == "missing":
        if parsed.pages:
            enriched.append({
                "page_no": 1,
                "bbox_ratio": [0.07, 0.01, 0.5, 0.04],
                "block_id": None,
                "severity": issue["severity"],
                "rule_id": issue["rule_id"],
            })

    if enriched:
        issue["highlights"] = enriched
        # 첫 번째 하이라이트의 page_no를 이슈 대표 페이지로
        issue["page_no"] = enriched[0]["page_no"]
        issue["bbox_ratio"] = enriched[0]["bbox_ratio"]