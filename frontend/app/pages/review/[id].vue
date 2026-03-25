<template>
  <div class="contents_wrap" id="contents_wrap">
    <!-- 헤더 -->
    <div class="header">
      <div class="left">
        <div class="pj_tit_wrap">
          <a href="/main" class="pj_img"
            ><img src="/img/layout/img_pj.svg" alt=""
          /></a>
          <span class="pj_tit txt">{{ projectTitle }}</span>
        </div>
      </div>
      <div class="right">
        <a href="/main" class="btn sz_s btn_ty05">
          <img src="/img/icon/ic_plus_w.svg" alt="" />신규
        </a>
        <div
          class="trigger_wrap member_util_trigger_wrap"
          id="member_util_trigger_wrap"
        >
          <a
            href="#;"
            class="trigger member_util_trigger"
            id="member_util_trigger"
          >
            <img src="/img/layout/img_profile_01.svg" alt="" />
          </a>
          <div
            class="trigger_toggle member_util_trigger_toggle"
            id="member_util_trigger_toggle"
          >
            <div class="member_wrap">
              <div class="member_info">
                <div class="member_name">서초구청 담당자 님</div>
              </div>
              <a href="#;" class="logout btn" @click="logout">
                <img src="/img/icon/ic_logout.svg" alt="" />로그아웃
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="contents_inn">
      <!-- ── 좌측: 문서 목록 -->
      <div class="contents_inn_box left_box" :class="{ open: leftOpen }">
        <div class="close_icons">
          <div class="top">
            <a
              href="#;"
              class="icon open_panel"
              @click.prevent="leftOpen = true"
            >
              <img src="/img/icon/ic_panel_menu.svg" alt="" />
            </a>
            <a href="#;" class="icon"
              ><img src="/img/icon/ic_panel_plus.svg" alt=""
            /></a>
          </div>
          <div class="btm">
            <a href="#;" class="icon"
              ><img src="/img/icon/ic_panel_start.svg" alt=""
            /></a>
          </div>
        </div>
        <div class="open_wrap">
          <div class="panel_top">
            <div class="tit_wrap">
              <div class="tit">문서</div>
              <a
                href="#;"
                class="icon close_panel"
                @click.prevent="leftOpen = false"
              >
                <img src="/img/icon/ic_panel_menu_close.svg" alt="" />
              </a>
            </div>
          </div>
          <div class="source_list_wrap">
            <div class="accordion">
              <div
                v-for="f in docFiles"
                :key="f.document_id"
                class="accordion_panel_item"
                :class="{ on: selectedDocId === f.document_id }"
                @click="selectDoc(f)"
              >
                <a href="#;" class="panel_item_tit_wrap" @click.prevent>
                  <div class="panel_item_tit">
                    <img src="/img/icon/ic_doc.svg" alt="" />
                    <span class="ellipsis">{{ f.filename }}</span>
                  </div>
                  <div class="panel_item_info">
                    <span class="badge" :class="docTypeBadge(f.doc_type)">{{
                      docTypeLabel(f.doc_type)
                    }}</span>
                    <span class="num ty_02">{{ f.issue_count }}건</span>
                  </div>
                </a>
              </div>
            </div>
          </div>
          <div class="panel_btm">
            <a href="/main" class="btn sz_md sq btn_ty05 btn_full">검토 시작</a>
          </div>
        </div>
      </div>

      <!-- ── 가운데: 문서뷰어 / 채팅 탭 -->
      <div class="contents_inn_box center_box">
        <div class="doc_wrap">
          <div class="doc_wrap_top">
            <div class="tab_menu" data-tab-group="viewer">
              <a
                href="#"
                class="tab_link"
                :class="{ on: activeTab === 'doc' }"
                @click.prevent="activeTab = 'doc'"
              >
                <span class="inn">문서 뷰어</span>
              </a>
              <a
                href="#"
                class="tab_link"
                :class="{ on: activeTab === 'chat' }"
                @click.prevent="activeTab = 'chat'"
              >
                <span class="inn">대화 형식</span>
              </a>
            </div>
            <a href="#;" class="icon" @click.prevent="showChatSetting = true">
              <img src="/img/icon/ic_filter.svg" alt="" />
            </a>
          </div>

          <!-- 문서 뷰어 탭 -->
          <div class="tab_con viewer_01" :class="{ on: activeTab === 'doc' }">
            <div class="doc_tit_wrap">
              <div class="doc_tit">
                <img src="/img/icon/ic_doc.svg" alt="" />
                <span class="ellipsis">{{
                  selectedDoc?.filename || "문서를 선택하세요"
                }}</span>
              </div>
              <div class="doc_page_wrap" v-if="currentPage">
                <div class="doc_current_page">{{ currentPage }}</div>
                <div class="doc_total_page">/ {{ totalPage }}</div>
              </div>
            </div>
            <div class="doc_viewer_wrap" ref="viewerEl">
              <!-- PDF.js 렌더링 영역 -->
              <div
                v-if="!selectedDoc"
                class="empty_wrap"
                style="padding: 40px; text-align: center"
              >
                <div class="txt_wrap">좌측에서 문서를 선택해주세요.</div>
              </div>
              <canvas
                v-else
                ref="pdfCanvas"
                style="width: 100%; height: auto; display: block"
              ></canvas>
              <!-- 하이라이트 오버레이 -->
              <svg
                v-if="selectedDoc && highlights.length"
                ref="hlSvg"
                style="
                  position: absolute;
                  top: 0;
                  left: 0;
                  width: 100%;
                  height: 100%;
                  pointer-events: none;
                "
                :viewBox="`0 0 ${canvasW} ${canvasH}`"
              >
                <rect
                  v-for="hl in currentPageHighlights"
                  :key="hl.issue_id"
                  :x="hl.bbox.x1"
                  :y="hl.bbox.y1"
                  :width="hl.bbox.x2 - hl.bbox.x1"
                  :height="hl.bbox.y2 - hl.bbox.y1"
                  :fill="hlColor(hl.color)"
                  :stroke="
                    hl.color === 'red'
                      ? '#ff4d6d'
                      : hl.color === 'orange'
                        ? '#ff8c42'
                        : '#f5c842'
                  "
                  stroke-width="1.5"
                  rx="2"
                  @mouseenter="hoveredIssueId = hl.issue_id"
                  @mouseleave="hoveredIssueId = null"
                  style="pointer-events: all; cursor: pointer"
                  @click="focusIssue(hl.issue_id)"
                />
                <!-- 툴팁 -->
                <g v-if="hoveredHighlight">
                  <rect
                    :x="hoveredHighlight.bbox.x1"
                    :y="hoveredHighlight.bbox.y1 - 28"
                    width="160"
                    height="22"
                    rx="4"
                    fill="#222"
                    opacity="0.9"
                  />
                  <text
                    :x="hoveredHighlight.bbox.x1 + 8"
                    :y="hoveredHighlight.bbox.y1 - 12"
                    fill="white"
                    font-size="11"
                  >
                    {{ hoveredHighlight.label }}
                  </text>
                </g>
              </svg>
            </div>
            <!-- 페이지 이동 -->
            <div
              v-if="selectedDoc && totalPage > 1"
              class="doc_page_nav"
              style="
                display: flex;
                justify-content: center;
                gap: 8px;
                padding: 8px;
              "
            >
              <button
                class="btn sz_s btn_ty04"
                :disabled="currentPage <= 1"
                @click="goPrevPage"
              >
                ◀
              </button>
              <span style="line-height: 32px; font-size: 13px"
                >{{ currentPage }} / {{ totalPage }}</span
              >
              <button
                class="btn sz_s btn_ty04"
                :disabled="currentPage >= totalPage"
                @click="goNextPage"
              >
                ▶
              </button>
            </div>
          </div>

          <!-- 채팅 탭 -->
          <div class="tab_con viewer_02" :class="{ on: activeTab === 'chat' }">
            <div class="result_talk_wrap">
              <!-- AI 메시지 -->
              <div class="talk_ai_wrap" v-if="summary">
                <div class="talk_doc_tit">
                  <img src="/img/icon/ic_doc.svg" alt="" />
                  <div class="txt">{{ selectedDoc?.filename }}</div>
                </div>
                <div class="talk_tit_01">묶음 문서 검토 결과</div>
                <div class="talk_txt">
                  문서를 검토해 본 결과, 현재 개정된 내부 문건 규정 기준
                  <span class="ty_01 mark_box"
                    >확인 필요
                    <span class="num">{{
                      summary.warning_issue_count
                    }}</span></span
                  >
                  <span class="ty_02 mark_box"
                    >위반
                    <span class="num">{{
                      summary.high_issue_count
                    }}</span></span
                  >
                  건의 수정요소가 확인되었습니다.
                </div>
                <div class="line"></div>
                <div class="talk_tit_02">결재선 안내</div>
                <div class="dot_list mt_20 mb_20 talk_txt" v-if="approvalLine">
                  <div
                    v-for="step in approvalLine.steps"
                    :key="step"
                    class="dot_item"
                  >
                    <span class="fw_b">{{ step }} </span>
                  </div>
                </div>
              </div>

              <!-- 대화 히스토리 -->
              <template v-for="(msg, i) in chatHistory" :key="i">
                <div v-if="msg.role === 'user'" class="talk_me_wrap">
                  <div class="talk_me_item">{{ msg.content }}</div>
                </div>
                <div v-else class="talk_ai_wrap">
                  <div
                    class="talk_txt"
                    v-html="msg.content.replace(/\n/g, '<br>')"
                  ></div>
                </div>
              </template>

              <!-- 스트리밍 중 -->
              <div v-if="isStreaming" class="talk_ai_wrap">
                <div
                  class="talk_txt"
                  v-html="streamingText.replace(/\n/g, '<br>')"
                ></div>
              </div>
            </div>
            <div class="result_talk_btm_wrap">
              <div class="result_talk_search_wrap">
                <input
                  v-model="chatInput"
                  type="text"
                  class="search_input"
                  placeholder="규정 또는 검토 질문을 검색해주세요."
                  @keyup.enter="sendChat"
                />
                <button class="search_btn" aria-label="검색" @click="sendChat">
                  <img src="/img/icon/ic_btn_search.svg" alt="" />
                </button>
              </div>
              <div class="alert_txt">
                <img src="/img/icon/ic_alert.svg" alt="" />
                Ai가 부정확한 정보를 표시할 수 있으므로 대답을 다시 한번
                확인하세요.
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── 우측: 이슈 카드 -->
      <div class="contents_inn_box right_box" :class="{ open: rightOpen }">
        <div class="close_icons">
          <div class="top">
            <a
              href="#;"
              class="icon open_panel"
              @click.prevent="rightOpen = true"
            >
              <img src="/img/icon/ic_panel_menu.svg" alt="" />
            </a>
            <a href="#;" class="icon"
              ><img src="/img/icon/ic_panel_result.svg" alt=""
            /></a>
          </div>
          <div class="btm">
            <a :href="reportDownloadUrl" class="icon" title="리포트 다운로드">
              <img src="/img/icon/ic_panel_down.svg" alt="" />
            </a>
            <a href="#;" class="icon" @click.prevent="showChecklist = true">
              <img src="/img/icon/ic_panel_check.svg" alt="" />
            </a>
          </div>
        </div>
        <div class="open_wrap">
          <div class="panel_top">
            <div class="tit_wrap">
              <div class="tit">리포트</div>
              <a
                href="#;"
                class="icon close_panel"
                @click.prevent="rightOpen = false"
              >
                <img src="/img/icon/ic_panel_menu_close.svg" alt="" />
              </a>
            </div>
            <a href="#;" class="btn sz_md sq btn_ty05 btn_full">검토 결과</a>
          </div>

          <!-- 요약 -->
          <div class="result_list_wrap ty_02">
            <div class="result_top">
              <div class="doc_ty_info">
                <div class="doc_ty_info_ic"></div>
                <div class="doc_ty_info_txt">
                  <div class="tit">
                    {{ docTypeLabel(selectedDoc?.doc_type) }} 문서입니다.
                  </div>
                </div>
              </div>
              <div class="legend_list">
                <div class="legend_item ty_01">
                  <img src="/img/icon/ic_legend_ty_01.svg" alt="" />
                  확인 필요
                  <span class="num">{{
                    countBySev("warning") + countBySev("info")
                  }}</span>
                </div>
                <div class="legend_item ty_02">
                  <img src="/img/icon/ic_legend_ty_02.svg" alt="" />
                  위반 <span class="num">{{ countBySev("critical") }}</span>
                </div>
                <div class="legend_item ty_03">
                  <img src="/img/icon/ic_legend_ty_03.svg" alt="" />
                  누락 <span class="num">{{ countByCat("missing") }}</span>
                </div>
                <div class="legend_item ty_04">
                  <img src="/img/icon/ic_legend_ty_04.svg" alt="" />
                  수치오류
                  <span class="num">{{
                    countByCat("typo") + countByCat("inconsistency")
                  }}</span>
                </div>
              </div>
            </div>

            <!-- 이슈 카드 목록 -->
            <div class="result_list">
              <div class="result_inn_list">
                <a
                  v-for="iss in currentDocIssues"
                  :key="iss.id"
                  href="#;"
                  class="result_inn_item"
                  :class="[
                    issueTypeClass(iss),
                    { on: focusedIssueId === iss.id },
                  ]"
                  @click.prevent="onIssueClick(iss)"
                >
                  <div class="item_tit_wrap">
                    <span class="mark">{{ issueTypeLabel(iss) }}</span>
                    <span class="tit ellipsis">{{ iss.title }}</span>
                  </div>
                  <div class="item_txt_wrap">{{ iss.description }}</div>
                  <div
                    v-if="iss.regulation_refs?.length"
                    class="item_info_wrap"
                  >
                    *{{ iss.regulation_refs[0].regulation_title }}
                  </div>
                </a>
              </div>
            </div>

            <div class="down_wrap">
              <a :href="reportDownloadUrl" class="btn sz_r btn_ty04">
                <img src="/img/icon/ic_down.svg" alt="" />리포트·문서 원본 다운
              </a>
            </div>
          </div>

          <div class="panel_btm">
            <button
              type="button"
              class="btn sz_md sq btn_ty02 btn_full"
              @click="showChecklist = true"
            >
              <img src="/img/icon/ic_check_p.svg" alt="" />체크리스트
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 체크리스트 팝업 -->
    <div class="dim" :class="{ open: showChecklist }">
      <div class="layer_popup pop_checklist" role="dialog" aria-modal="true">
        <button
          type="button"
          class="ic_close pop_close"
          @click="showChecklist = false"
        ></button>
        <div class="popup_header">체크리스트</div>
        <div class="popup_body">
          <div v-if="checklistItems.length">
            <div
              v-for="item in checklistItems"
              :key="item.item_code"
              class="checklist_item_row"
              style="
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 8px 0;
                border-bottom: 1px solid #eee;
              "
            >
              <span
                class="badge"
                :class="item.result === 'pass' ? 'ty_pass' : 'ty_fail'"
              >
                {{ item.result === "pass" ? "✓" : "✗" }}
              </span>
              <div style="flex: 1">
                <div style="font-size: 13px; font-weight: 600">
                  {{ item.title }}
                </div>
                <div style="font-size: 12px; color: #888">
                  {{ item.comment }}
                </div>
              </div>
            </div>
          </div>
          <div v-else style="text-align: center; padding: 20px; color: #aaa">
            로딩 중...
          </div>
        </div>
        <div class="popup_footer">
          <button
            type="button"
            class="btn sz_r btn_ty02"
            @click="showChecklist = false"
          >
            닫기
          </button>
        </div>
      </div>
    </div>

    <!-- ── 채팅 설정 팝업 -->
    <div class="dim" :class="{ open: showChatSetting }">
      <div class="layer_popup pop_set_chat" id="pop_set_chat" role="dialog">
        <button
          type="button"
          class="ic_close pop_close"
          @click="showChatSetting = false"
        ></button>
        <div class="popup_header">채팅 설정</div>
        <div class="popup_body">
          <div class="set_chat_txt">대답 길이를 선택하세요.</div>
          <div class="set_chat_choice_tit">대답 길이 선택</div>
          <div class="choice_list_02">
            <a
              v-for="opt in ['기본값', '길게', '짧게']"
              :key="opt"
              href="#;"
              class="choice_item"
              :class="{ on: chatLength === opt }"
              @click.prevent="chatLength = opt"
              >{{ opt }}</a
            >
          </div>
        </div>
        <div class="popup_footer">
          <button
            type="button"
            class="btn sz_r btn_ty02"
            @click="showChatSetting = false"
          >
            저장
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRouter();
const rroute = useRoute();
const runId = computed(() => Number(rroute.params.id));

const {
  getDocuments,
  getIssues,
  getIssueSummary,
  getHighlights,
  getChecklist,
  getApprovalLine,
  getReportDownloadUrl,
  chatStream,
} = useApi();

// ── 상태
const projectTitle = ref("AI 계약서류 검토");
const leftOpen = ref(true);
const rightOpen = ref(true);
const activeTab = ref<"doc" | "chat">("doc");
const showChecklist = ref(false);
const showChatSetting = ref(false);
const chatLength = ref("기본값");

const docFiles = ref<any[]>([]);
const selectedDoc = ref<any>(null);
const selectedDocId = computed(() => selectedDoc.value?.document_id);
const issues = ref<any[]>([]);
const summary = ref<any>(null);
const highlights = ref<any[]>([]);
const approvalLine = ref<any>(null);
const checklistItems = ref<any[]>([]);

// 채팅
const chatHistory = ref<{ role: string; content: string }[]>([]);
const chatInput = ref("");
const isStreaming = ref(false);
const streamingText = ref("");

// PDF 뷰어
const pdfCanvas = ref<HTMLCanvasElement>();
const viewerEl = ref<HTMLElement>();
const hlSvg = ref<SVGElement>();
const currentPage = ref(1);
const totalPage = ref(1);
const canvasW = ref(595);
const canvasH = ref(842);
const hoveredIssueId = ref<number | null>(null);
const focusedIssueId = ref<number | null>(null);
let pdfDoc: any = null;

const reportDownloadUrl = computed(() => getReportDownloadUrl(runId.value));

// ── 현재 문서 이슈
const currentDocIssues = computed(() =>
  selectedDocId.value
    ? issues.value.filter((i) => i.document_id === selectedDocId.value)
    : issues.value,
);

// ── 현재 페이지 하이라이트
const currentPageHighlights = computed(() =>
  highlights.value.filter((h) => h.page_no === currentPage.value),
);

const hoveredHighlight = computed(() =>
  hoveredIssueId.value
    ? currentPageHighlights.value.find(
        (h) => h.issue_id === hoveredIssueId.value,
      )
    : null,
);

// ── 초기 로드
onMounted(async () => {
  if (!localStorage.getItem("clms_logged_in")) {
    route.push("/");
    return;
  }
  document.addEventListener("click", handleTrigger);
  await loadAll();
});
onUnmounted(() => document.removeEventListener("click", handleTrigger));

async function loadAll() {
  try {
    const [docsRes, issRes, sumRes, apvRes] = await Promise.all([
      getDocuments(runId.value),
      getIssues(runId.value),
      getIssueSummary(runId.value),
      getApprovalLine(runId.value),
    ]);
    docFiles.value = (docsRes as any).data?.items || [];
    issues.value = (issRes as any).data?.items || [];
    summary.value = (sumRes as any).data;
    approvalLine.value = (apvRes as any).data;

    if (docFiles.value.length) selectDoc(docFiles.value[0]);
    await loadChecklist();
  } catch (e) {
    console.error("데이터 로드 실패", e);
  }
}

async function selectDoc(f: any) {
  selectedDoc.value = f;
  currentPage.value = 1;
  highlights.value = [];
  focusedIssueId.value = null;

  // 하이라이트 로드
  try {
    const hlRes = await getHighlights(runId.value, f.document_id);
    highlights.value = (hlRes as any).data?.items || [];
  } catch {}

  // PDF 렌더
  await renderPdf(f);
}

async function renderPdf(f: any) {
  if (!pdfCanvas.value) return;
  try {
    // MinIO PDF URL: /api/v1/projects/1/reviews/{runId}/pdf/{docId}
    // 또는 직접 파일 경로 사용 — PoC에서는 MinIO URL로
    const url = `/api/v1/projects/1/reviews/${runId.value}/pdf/${f.document_id}`;
    // @ts-ignore
    const pdfjsLib = window.pdfjsLib;
    if (!pdfjsLib) {
      console.warn("pdf.js 미로드");
      return;
    }

    pdfjsLib.GlobalWorkerOptions.workerSrc = "/js/pdf.worker.min.js";
    pdfDoc = await pdfjsLib.getDocument(url).promise;
    totalPage.value = pdfDoc.numPages;
    await renderPage(currentPage.value);
  } catch (e) {
    console.warn("PDF 렌더 실패:", e);
  }
}

async function renderPage(pageNum: number) {
  if (!pdfDoc || !pdfCanvas.value) return;
  const page = await pdfDoc.getPage(pageNum);
  const viewport = page.getViewport({ scale: 1.5 });
  canvasW.value = viewport.width;
  canvasH.value = viewport.height;
  pdfCanvas.value.width = viewport.width;
  pdfCanvas.value.height = viewport.height;
  await page.render({
    canvasContext: pdfCanvas.value.getContext("2d")!,
    viewport,
  }).promise;
}

function goPrevPage() {
  if (currentPage.value > 1) {
    currentPage.value--;
    renderPage(currentPage.value);
  }
}
function goNextPage() {
  if (currentPage.value < totalPage.value) {
    currentPage.value++;
    renderPage(currentPage.value);
  }
}

function onIssueClick(iss: any) {
  focusedIssueId.value = iss.id;
  // 해당 이슈 페이지로 이동
  const hl = highlights.value.find((h) => h.issue_id === iss.id);
  if (hl && hl.page_no !== currentPage.value) {
    currentPage.value = hl.page_no;
    renderPage(hl.page_no);
  }
  // 문서 뷰어 탭으로 전환
  activeTab.value = "doc";
}

function focusIssue(issueId: number) {
  focusedIssueId.value = issueId;
}

async function loadChecklist() {
  try {
    const res = await getChecklist(runId.value);
    checklistItems.value = (res as any).data?.items || [];
  } catch {}
}

// ── 채팅
async function sendChat() {
  const q = chatInput.value.trim();
  if (!q || isStreaming.value) return;
  chatInput.value = "";
  chatHistory.value.push({ role: "user", content: q });
  isStreaming.value = true;
  streamingText.value = "";

  chatStream(
    q,
    runId.value,
    selectedDocId.value || 0,
    (chunk) => {
      streamingText.value += chunk;
    },
    () => {
      chatHistory.value.push({
        role: "assistant",
        content: streamingText.value,
      });
      streamingText.value = "";
      isStreaming.value = false;
    },
    (err) => {
      chatHistory.value.push({ role: "assistant", content: `오류: ${err}` });
      isStreaming.value = false;
    },
  );
}

// ── 헬퍼
function handleTrigger(e: MouseEvent) {
  const el = (e.target as HTMLElement).closest(
    ".trigger",
  ) as HTMLElement | null;
  if (!el) return;
  const id = el.getAttribute("id");
  if (!id) return;
  const wrap = document.getElementById(id + "_wrap");
  const toggle = document.getElementById(id + "_toggle");
  if (wrap) wrap.classList.toggle("open");
  if (toggle) toggle.classList.toggle("open");
  el.classList.toggle("open");
}

function docTypeLabel(t?: string) {
  return (
    {
      bid_notice: "입찰공고문",
      proposal_request: "제안요청서",
      plan: "계획서",
    }[t || ""] || "문서"
  );
}
function docTypeBadge(t?: string) {
  return (
    { bid_notice: "ty_bid", proposal_request: "ty_rfp", plan: "ty_plan" }[
      t || ""
    ] || ""
  );
}

function issueTypeClass(iss: any) {
  if (iss.severity === "critical") return "ty_02";
  if (iss.category === "missing") return "ty_03";
  if (iss.category === "typo" || iss.category === "inconsistency")
    return "ty_04";
  return "ty_01";
}
function issueTypeLabel(iss: any) {
  if (iss.severity === "critical") return "위반";
  if (iss.category === "missing") return "누락";
  if (iss.category === "typo" || iss.category === "inconsistency")
    return "수치 오류";
  return "확인 필요";
}

function hlColor(c: string) {
  return (
    {
      red: "rgba(255,77,109,0.25)",
      orange: "rgba(255,140,66,0.25)",
      yellow: "rgba(245,200,66,0.25)",
      blue: "rgba(79,195,247,0.2)",
    }[c] || "rgba(245,200,66,0.2)"
  );
}

function countBySev(sev: string) {
  return currentDocIssues.value.filter((i) => i.severity === sev).length;
}
function countByCat(cat: string) {
  return currentDocIssues.value.filter((i) => i.category === cat).length;
}

function logout() {
  localStorage.removeItem("clms_logged_in");
  route.push("/");
}
</script>
