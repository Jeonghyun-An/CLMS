"""
AI 계약서류 검토 PDF 리포트 생성기
────────────────────────────────────────────────────────────
입력:  이슈 목록 (reviews.py의 _review_store 결과)
출력:  BytesIO (PDF 바이너리) — FastAPI StreamingResponse로 반환

폰트:  NanumGothic (서버에 fonts-nanum 패키지 필요)
       Docker: apt-get install -y fonts-nanum
"""

from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

# ──────────────────────────────────────────────
# 폰트 등록 (최초 1회)
# ──────────────────────────────────────────────

FONT_DIR = os.getenv("FONT_DIR", "/usr/share/fonts/truetype/nanum")

_fonts_registered = False

def _register_fonts():
    global _fonts_registered
    if _fonts_registered:
        return
    try:
        pdfmetrics.registerFont(TTFont("Nanum",     f"{FONT_DIR}/NanumGothic.ttf"))
        pdfmetrics.registerFont(TTFont("NanumBold", f"{FONT_DIR}/NanumGothicBold.ttf"))
    except Exception:
        # 폰트 없으면 Helvetica로 폴백 (한글 깨짐 — 개발 환경용)
        pdfmetrics.registerFont(TTFont("Nanum",     "Helvetica"))
        pdfmetrics.registerFont(TTFont("NanumBold", "Helvetica-Bold"))
    _fonts_registered = True


# ──────────────────────────────────────────────
# 색상 팔레트
# ──────────────────────────────────────────────

C = {
    "black":    colors.HexColor("#111111"),
    "white":    colors.white,
    "bg":       colors.HexColor("#f8f9fa"),
    "border":   colors.HexColor("#dee2e6"),
    "header":   colors.HexColor("#1a1a2e"),
    "accent":   colors.HexColor("#4f7cff"),

    "critical": colors.HexColor("#ff4d6d"),
    "high":     colors.HexColor("#ff8c42"),
    "warning":  colors.HexColor("#f5c842"),
    "info":     colors.HexColor("#4fc3f7"),
    "pass_":    colors.HexColor("#4caf87"),

    "critical_bg": colors.HexColor("#fff0f3"),
    "high_bg":     colors.HexColor("#fff4ee"),
    "warning_bg":  colors.HexColor("#fffbe6"),
    "info_bg":     colors.HexColor("#f0faff"),
    "row_alt":     colors.HexColor("#f5f5f5"),
}

SEV_KO = {"critical": "위험", "high": "높음", "warning": "경고", "info": "정보"}
CAT_KO = {
    "missing":              "누락",
    "regulation_violation": "법령위반",
    "inconsistency":        "불일치",
    "typo":                 "표기오류",
    "approval_rule":        "결재선",
}


# ──────────────────────────────────────────────
# 스타일
# ──────────────────────────────────────────────

def _styles() -> dict[str, ParagraphStyle]:
    return {
        "cover_title": ParagraphStyle(
            "ct", fontName="NanumBold", fontSize=24,
            alignment=TA_CENTER, textColor=C["white"], spaceAfter=4,
        ),
        "cover_sub": ParagraphStyle(
            "cs", fontName="Nanum", fontSize=11,
            alignment=TA_CENTER, textColor=colors.HexColor("#aaaacc"), spaceAfter=2,
        ),
        "section": ParagraphStyle(
            "sec", fontName="NanumBold", fontSize=13,
            textColor=C["black"], spaceBefore=8, spaceAfter=4,
            borderPad=2,
        ),
        "body": ParagraphStyle(
            "bd", fontName="Nanum", fontSize=9.5,
            textColor=C["black"], leading=16, spaceAfter=3,
        ),
        "small": ParagraphStyle(
            "sm", fontName="Nanum", fontSize=8,
            textColor=colors.HexColor("#666666"), leading=13,
        ),
        "card_title": ParagraphStyle(
            "crt", fontName="NanumBold", fontSize=10,
            textColor=C["black"], spaceAfter=2,
        ),
        "card_body": ParagraphStyle(
            "crb", fontName="Nanum", fontSize=9,
            textColor=colors.HexColor("#333333"), leading=14, spaceAfter=2,
        ),
        "card_law": ParagraphStyle(
            "crl", fontName="Nanum", fontSize=8.5,
            textColor=C["accent"], leading=13,
        ),
        "label": ParagraphStyle(
            "lbl", fontName="NanumBold", fontSize=8,
            textColor=C["white"],
        ),
        "tbl_hdr": ParagraphStyle(
            "th", fontName="NanumBold", fontSize=9, textColor=C["white"],
        ),
        "tbl_cell": ParagraphStyle(
            "tc", fontName="Nanum", fontSize=9, textColor=C["black"], leading=13,
        ),
    }


# ──────────────────────────────────────────────
# 페이지 번호 콜백
# ──────────────────────────────────────────────

class _PageNum:
    def __init__(self, doc_title: str):
        self.doc_title = doc_title

    def __call__(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Nanum", 8)
        canvas.setFillColor(colors.HexColor("#888888"))
        w, h = A4
        canvas.drawString(20*mm, 12*mm, self.doc_title)
        canvas.drawRightString(w - 20*mm, 12*mm, f"{doc.page}")
        canvas.restoreState()


# ──────────────────────────────────────────────
# 표지
# ──────────────────────────────────────────────

def _make_cover(story: list, meta: dict, st: dict):
    w, h = A4
    # 배경 블록 (Table 트릭으로 색상 배경 구현)
    cover_data = [[""]]
    cover_tbl = Table(cover_data, colWidths=[w - 40*mm], rowHeights=[60*mm])
    cover_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C["header"]),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(Spacer(1, 10*mm))
    story.append(cover_tbl)

    # 제목 텍스트 (오버레이 효과 대신 바로 출력)
    story.append(Spacer(1, -58*mm))  # 위로 올리기
    story.append(Paragraph("AI 계약서류 검토 리포트", st["cover_title"]))
    story.append(Paragraph(meta.get("project_name", "서초구 계약서류 검토"), st["cover_sub"]))
    story.append(Spacer(1, 55*mm))

    # 메타 정보 표
    now = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    meta_data = [
        ["검토 일시", now],
        ["발주기관",  meta.get("issuer", "서초구청 스마트도시과")],
        ["문서 수",   f"{meta.get('doc_count', 1)}건"],
        ["총 이슈",   f"{meta.get('total_issues', 0)}건"],
    ]
    meta_tbl = Table(meta_data, colWidths=[35*mm, 120*mm])
    meta_tbl.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (0, -1), "NanumBold"),
        ("FONTNAME",    (1, 0), (1, -1), "Nanum"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR",   (0, 0), (0, -1), colors.HexColor("#555555")),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW",   (0, 0), (-1, -2), 0.3, C["border"]),
    ]))
    story.append(meta_tbl)
    story.append(PageBreak())


# ──────────────────────────────────────────────
# 요약 섹션
# ──────────────────────────────────────────────

def _make_summary(story: list, issues: list[dict], st: dict):
    counts = {"critical": 0, "high": 0, "warning": 0, "info": 0}
    for iss in issues:
        sev = iss.get("severity", "info")
        counts[sev] = counts.get(sev, 0) + 1

    total = len(issues)
    if counts["critical"] + counts["high"] > 0:
        verdict = "❌  검토 필요 (위반 사항 있음)"
        verdict_color = C["critical"]
    elif counts["warning"] > 0:
        verdict = "⚠  조건부 적합 (경고 사항 확인 필요)"
        verdict_color = C["warning"]
    else:
        verdict = "✅  적합"
        verdict_color = C["pass_"]

    story.append(Paragraph("📋  검토 요약", st["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C["border"]))
    story.append(Spacer(1, 3*mm))

    # 종합 판정 박스
    verdict_data = [[verdict]]
    verdict_tbl = Table(verdict_data, colWidths=[165*mm])
    verdict_tbl.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (-1, -1), "NanumBold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 12),
        ("TEXTCOLOR",   (0, 0), (-1, -1), verdict_color),
        ("BACKGROUND",  (0, 0), (-1, -1), C["bg"]),
        ("BOX",         (0, 0), (-1, -1), 1, C["border"]),
        ("TOPPADDING",  (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(verdict_tbl)
    story.append(Spacer(1, 4*mm))

    # 이슈 수 카드
    sev_info = [
        ("위험",  counts["critical"], C["critical"],    C["critical_bg"]),
        ("높음",  counts["high"],     C["high"],         C["high_bg"]),
        ("경고",  counts["warning"],  C["warning"],      C["warning_bg"]),
        ("정보",  counts["info"],     C["info"],         C["info_bg"]),
        ("합계",  total,              C["accent"],       C["bg"]),
    ]
    card_data = [[f"{label}\n{cnt}건" for label, cnt, *_ in sev_info]]
    card_colors_bg  = [bg  for *_, fg, bg in sev_info]
    card_colors_fg  = [fg  for *_, fg, bg in sev_info]

    card_tbl = Table(card_data, colWidths=[33*mm]*5)
    style_cmds = [
        ("FONTNAME",    (0, 0), (-1, -1), "NanumBold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BOX",         (0, 0), (-1, -1), 0.5, C["border"]),
        ("INNERGRID",   (0, 0), (-1, -1), 0.5, C["border"]),
    ]
    for i, (_, _, fg, bg) in enumerate(sev_info):
        style_cmds.append(("BACKGROUND",  (i, 0), (i, 0), bg))
        style_cmds.append(("TEXTCOLOR",   (i, 0), (i, 0), fg))
    card_tbl.setStyle(TableStyle(style_cmds))
    story.append(card_tbl)
    story.append(Spacer(1, 6*mm))


# ──────────────────────────────────────────────
# 이슈 목록 표
# ──────────────────────────────────────────────

def _make_issue_table(story: list, issues: list[dict], st: dict):
    story.append(Paragraph("📌  이슈 목록", st["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C["border"]))
    story.append(Spacer(1, 3*mm))

    if not issues:
        story.append(Paragraph("발견된 이슈가 없습니다.", st["body"]))
        return

    hdr = ["No.", "룰ID", "심각도", "분류", "제목"]
    rows = [hdr]
    for i, iss in enumerate(issues, 1):
        sev = iss.get("severity", "info")
        rows.append([
            str(i),
            iss.get("rule_id", "—"),
            SEV_KO.get(sev, sev),
            CAT_KO.get(iss.get("category", ""), iss.get("category", "—")),
            iss.get("title", "—"),
        ])

    tbl = Table(rows, colWidths=[10*mm, 15*mm, 15*mm, 20*mm, 105*mm])
    sev_colors = {
        "위험": C["critical"], "높음": C["high"],
        "경고": C["warning"],  "정보": C["info"],
    }
    style_cmds = [
        ("FONTNAME",    (0, 0), (-1, 0),  "NanumBold"),
        ("FONTNAME",    (0, 1), (-1, -1), "Nanum"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("BACKGROUND",  (0, 0), (-1, 0),  C["header"]),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  C["white"]),
        ("ALIGN",       (0, 0), (3, -1),  "CENTER"),
        ("ALIGN",       (4, 0), (4, -1),  "LEFT"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0,0), (-1, -1), 5),
        ("GRID",        (0, 0), (-1, -1), 0.4, C["border"]),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),  [C["white"], C["row_alt"]]),
    ]
    # 심각도 셀 색상
    for r, row in enumerate(rows[1:], 1):
        sev_label = row[2]
        fg = sev_colors.get(sev_label, C["black"])
        style_cmds.append(("TEXTCOLOR", (2, r), (2, r), fg))
        style_cmds.append(("FONTNAME",  (2, r), (2, r), "NanumBold"))

    tbl.setStyle(TableStyle(style_cmds))
    story.append(tbl)
    story.append(Spacer(1, 6*mm))


# ──────────────────────────────────────────────
# 이슈 상세 카드
# ──────────────────────────────────────────────

def _make_issue_details(story: list, issues: list[dict], st: dict):
    story.append(Paragraph("🔍  이슈 상세", st["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C["border"]))
    story.append(Spacer(1, 3*mm))

    sev_colors = {
        "critical": C["critical"], "high": C["high"],
        "warning":  C["warning"],  "info": C["info"],
    }
    sev_bg = {
        "critical": C["critical_bg"], "high": C["high_bg"],
        "warning":  C["warning_bg"],  "info": C["info_bg"],
    }

    for i, iss in enumerate(issues, 1):
        sev      = iss.get("severity", "info")
        fg       = sev_colors.get(sev, C["black"])
        bg       = sev_bg.get(sev, C["bg"])
        sev_text = f"[{SEV_KO.get(sev, sev)}]  {iss.get('rule_id', '')}  {iss.get('title', '')}"

        # 카드 헤더
        hdr_data = [[sev_text]]
        hdr_tbl = Table(hdr_data, colWidths=[165*mm])
        hdr_tbl.setStyle(TableStyle([
            ("FONTNAME",    (0,0), (-1,-1), "NanumBold"),
            ("FONTSIZE",    (0,0), (-1,-1), 10),
            ("TEXTCOLOR",   (0,0), (-1,-1), fg),
            ("BACKGROUND",  (0,0), (-1,-1), bg),
            ("TOPPADDING",  (0,0), (-1,-1), 6),
            ("BOTTOMPADDING",(0,0),(-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("BOX",         (0,0), (-1,-1), 0.8, fg),
        ]))
        story.append(hdr_tbl)

        # 카드 본문
        body_rows = []
        if iss.get("description"):
            body_rows.append(["설명", iss["description"]])
        if iss.get("recommendation"):
            body_rows.append(["권고", iss["recommendation"]])
        if iss.get("regulation_refs"):
            refs = iss["regulation_refs"]
            ref_text = refs[0].get("regulation_title", "") if refs else ""
            if ref_text:
                body_rows.append(["근거", ref_text])
        if iss.get("evidences"):
            ev = iss["evidences"][0]
            qt = ev.get("quoted_text", "")
            pn = ev.get("page_no", "")
            if qt:
                loc = f"(p.{pn}) " if pn else ""
                body_rows.append(["원문", f"{loc}{qt[:100]}"])
        src = "📐 룰엔진" if iss.get("source") == "rule" else "🤖 AI분석"
        body_rows.append(["출처", src])

        if body_rows:
            body_tbl = Table(body_rows, colWidths=[15*mm, 150*mm])
            body_tbl.setStyle(TableStyle([
                ("FONTNAME",    (0,0), (0,-1), "NanumBold"),
                ("FONTNAME",    (1,0), (1,-1), "Nanum"),
                ("FONTSIZE",    (0,0), (-1,-1), 9),
                ("TEXTCOLOR",   (0,0), (0,-1), colors.HexColor("#555555")),
                ("VALIGN",      (0,0), (-1,-1), "TOP"),
                ("TOPPADDING",  (0,0), (-1,-1), 4),
                ("BOTTOMPADDING",(0,0),(-1,-1), 4),
                ("LEFTPADDING", (0,0), (-1,-1), 8),
                ("LINEBELOW",   (0,0), (-1,-2), 0.3, C["border"]),
                ("BACKGROUND",  (0,0), (-1,-1), C["white"]),
                ("BOX",         (0,0), (-1,-1), 0.4, C["border"]),
            ]))
            story.append(body_tbl)

        story.append(Spacer(1, 4*mm))


# ──────────────────────────────────────────────
# 결재선 섹션
# ──────────────────────────────────────────────

def _make_approval_section(story: list, approval: dict | None, st: dict):
    if not approval:
        return
    story.append(Paragraph("✍  결재선 안내", st["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C["border"]))
    story.append(Spacer(1, 3*mm))

    steps = approval.get("steps", [])
    rule_name = approval.get("rule_name", "")
    ref_text  = approval.get("reference_text", "")

    story.append(Paragraph(f"적용 규정: {rule_name}", st["body"]))
    story.append(Paragraph(f"근거: {ref_text}", st["small"]))
    story.append(Spacer(1, 3*mm))

    if steps:
        step_row = [" → ".join(steps)]
        step_tbl = Table([step_row], colWidths=[165*mm])
        step_tbl.setStyle(TableStyle([
            ("FONTNAME",    (0,0), (-1,-1), "NanumBold"),
            ("FONTSIZE",    (0,0), (-1,-1), 11),
            ("TEXTCOLOR",   (0,0), (-1,-1), C["accent"]),
            ("BACKGROUND",  (0,0), (-1,-1), C["bg"]),
            ("ALIGN",       (0,0), (-1,-1), "CENTER"),
            ("TOPPADDING",  (0,0), (-1,-1), 10),
            ("BOTTOMPADDING",(0,0),(-1,-1), 10),
            ("BOX",         (0,0), (-1,-1), 1, C["border"]),
        ]))
        story.append(step_tbl)
    story.append(Spacer(1, 6*mm))


# ──────────────────────────────────────────────
# 메인 함수
# ──────────────────────────────────────────────

def generate_report_pdf(
    issues: list[dict],
    meta: dict | None = None,
    approval: dict | None = None,
) -> bytes:
    """
    검토 이슈 목록을 받아 PDF 리포트 바이트 반환.

    Args:
        issues:   issues_to_api_response() 결과 리스트
        meta:     { project_name, issuer, doc_count, total_issues }
        approval: ApprovalLineResponse dict

    Returns:
        bytes: PDF 바이너리

    사용법 (reports.py에서):
        from app.services.review.report_generator import generate_report_pdf
        from fastapi.responses import Response

        pdf_bytes = generate_report_pdf(issues, meta, approval)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=review_report.pdf"}
        )
    """
    _register_fonts()
    st = _styles()

    if meta is None:
        meta = {}
    meta.setdefault("total_issues", len(issues))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title="AI 계약서류 검토 리포트",
        author="서초구 AI 계약검토시스템",
    )

    story: list = []
    page_cb = _PageNum("AI 계약서류 검토 리포트")

    _make_cover(story, meta, st)
    _make_summary(story, issues, st)
    _make_approval_section(story, approval, st)
    _make_issue_table(story, issues, st)
    story.append(PageBreak())
    _make_issue_details(story, issues, st)

    doc.build(story, onFirstPage=page_cb, onLaterPages=page_cb)
    return buf.getvalue()