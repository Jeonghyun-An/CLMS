<template>
  <div class="contents_wrap" id="contents_wrap">
    <ul class="skip_menu">
      <li><a href="#contents_wrap">본문 바로가기</a></li>
    </ul>
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
        <!-- 멤버 목록 -->
        <div class="trigger_wrap member_trigger_wrap" id="member_trigger_wrap">
          <a href="#;" class="trigger member_trigger" id="member_trigger">
            3명 참여<img src="/img/icon/ic_member.svg" alt="" />
          </a>
          <div
            class="trigger_toggle member_trigger_toggle"
            id="member_trigger_toggle"
          >
            <div class="member_trigger_list">
              <a href="#;" class="member_trigger_item">
                <div class="member_trigger_item_inn">
                  <div class="name_wrap">
                    <div class="img_wrap">
                      <img src="/img/layout/img_profile_01.svg" alt="" />
                    </div>
                    <div class="name">최승환</div>
                  </div>
                  <div class="position">스마트도시과 / 주무관</div>
                </div>
              </a>
              <a href="#;" class="member_trigger_item">
                <div class="member_trigger_item_inn">
                  <div class="name_wrap">
                    <div class="img_wrap">
                      <img src="/img/layout/img_profile_02.svg" alt="" />
                    </div>
                    <div class="name">홍길동</div>
                  </div>
                  <div class="position">스마트도시과 / 팀장</div>
                </div>
              </a>
            </div>
          </div>
        </div>

        <!-- 신규 -->
        <a href="/main" class="btn sz_s btn_ty05">
          <img src="/img/icon/ic_plus_w.svg" alt="" />신규
        </a>

        <!-- 관리자 -->
        <a href="#;" class="btn sz_s btn_ty04">
          <img src="/img/icon/ic_admin.svg" alt="" class="ic_color" />관리자
        </a>

        <!-- 공유 -->
        <div class="trigger_wrap share_trigger_wrap" id="share_trigger_wrap">
          <a
            href="#;"
            class="btn sz_s btn_ty04 trigger share_trigger"
            id="share_trigger"
          >
            <img src="/img/icon/ic_share.svg" alt="" class="ic_color" />공유
          </a>
          <div
            class="trigger_toggle share_trigger_toggle"
            id="share_trigger_toggle"
          >
            <div class="share_trigger_tit_wrap">
              <div class="share_trigger_tit">해당 파일 공유</div>
              <a
                href="#;"
                class="share_trigger_close trigger_close"
                aria-label="공유 닫기"
                @click.prevent="closeTrigger('share_trigger')"
              >
                <img src="/img/icon/ic_close.svg" alt="" />
              </a>
            </div>
            <div class="add_member">
              <input
                type="text"
                class="add_member_input"
                placeholder="사용자 및 그룹 추가"
              />
              <button class="add_member_btn btn sz_s sq">초대</button>
            </div>
            <div class="is_accessible">엑세스 권한이 있는 사람</div>
            <div class="share_trigger_list">
              <div
                class="share_trigger_item"
                v-for="(m, i) in [
                  { name: '누구나' },
                  { name: '최승환' },
                  { name: '홍길동' },
                ]"
                :key="i"
              >
                <div class="share_trigger_item_inn">
                  <a href="#;" class="name_wrap">
                    <div class="img_wrap">
                      <img
                        :src="'/img/layout/img_profile_0' + (i + 1) + '.svg'"
                        alt=""
                      />
                    </div>
                    <div class="name">{{ m.name }}</div>
                  </a>
                  <div class="select_box">
                    <select>
                      <option>소유자</option>
                      <option selected>볼 수 있음</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 메뉴 -->
        <a href="/library" class="btn sz_s hover_bg_01 btn_menu">
          <img src="/img/icon/ic_menu.svg" aria-label="메뉴" alt="" />
        </a>

        <!-- 내 계정 -->
        <div
          class="member_util_wrap trigger_wrap"
          id="member_util_trigger_wrap"
        >
          <a
            href="#;"
            class="btn sz_s hover_bg_01 trigger member_util_trigger"
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
                <div class="member_name">서초구청 님</div>
                <div class="member_email ellipsis">seocho@seoul.go.kr</div>
              </div>
              <a href="#;" class="logout btn" @click.prevent="logout">
                <img src="/img/icon/ic_logout.svg" alt="" />로그아웃
              </a>
            </div>
            <ul class="member_util_list">
              <li class="member_util_item">
                <a href="#;" class="util_item_inn">
                  <span class="ic ic_bookmark"></span>
                  <span class="txt">내 즐겨찾기</span>
                </a>
              </li>
              <li class="member_util_item">
                <a href="#;" class="util_item_inn">
                  <span class="ic ic_history"></span>
                  <span class="txt">내 검색기록</span>
                </a>
              </li>
              <li
                class="member_util_item lang_trigger_wrap trigger_wrap"
                id="lang_trigger_wrap"
              >
                <a href="#;" class="util_item_inn trigger" id="lang_trigger">
                  <span class="ic ic_lang"></span>
                  <span class="txt"
                    >표시언어: <span class="fw_b lang">한국어</span></span
                  >
                </a>
                <div
                  class="trigger_toggle lang_trigger_toggle"
                  id="lang_trigger_toggle"
                >
                  <div class="lang_trigger_toggle_hd">
                    <img src="/img/icon/ic_lang.svg" alt="" />표시언어
                  </div>
                  <ul class="lang_list">
                    <li class="lang_item">
                      <a href="#;" class="inn">English</a>
                    </li>
                    <li class="lang_item on">
                      <a href="#;" class="inn">한국어</a>
                    </li>
                  </ul>
                  <a
                    href="#;"
                    class="btn bg_black sz_md trigger_close"
                    data-target="lang_trigger"
                    @click.prevent="closeTrigger('lang_trigger')"
                    >취소</a
                  >
                </div>
              </li>
            </ul>
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
            <div class="source_list">
              <div class="list_num">
                총 문서 개수 <span class="num">{{ docFiles.length }}</span>
              </div>
              <div class="accordion">
                <!-- 카테고리별 그룹 아코디언 -->
                <div
                  v-for="group in docGroups"
                  :key="group.label"
                  class="accordion_item"
                  :class="{ open: group.open }"
                >
                  <button
                    type="button"
                    class="accordion_btn"
                    :aria-expanded="group.open"
                    @click="group.open = !group.open"
                  >
                    <span class="ellipsis">{{ group.label }}</span>
                  </button>
                  <div class="accordion_panel" :hidden="!group.open">
                    <div
                      v-for="f in group.files"
                      :key="f.document_id"
                      class="accordion_panel_item"
                      :class="{ on: selectedDocId === f.document_id }"
                      @click="selectDoc(f)"
                    >
                      <a href="#;" class="panel_item_tit_wrap" @click.prevent>
                        <div class="img_wrap">
                          <img :src="fileIcon(f.filename)" alt="" />
                        </div>
                        <div class="tit ellipsis">{{ f.filename }}</div>
                      </a>
                      <a
                        href="#;"
                        class="ic_del"
                        aria-label="항목 제거"
                        @click.prevent="removeDoc(f.document_id)"
                      ></a>
                    </div>
                  </div>
                </div>
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

          <div class="tab_con_wrap" data-tab-group="viewer">
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
                <!-- 선택 전 -->
                <div v-if="!selectedDoc" class="empty_wrap">
                  <div class="txt_wrap">좌측에서 문서를 선택해주세요.</div>
                </div>
                <!-- PDF.js iframe + 하이라이트 오버레이 -->
                <div v-else class="pdf_viewer_inner">
                  <iframe
                    :id="`pdf-viewer-${selectedDocId}`"
                    :src="pdfViewerUrl"
                    class="pdf_iframe"
                    @load="onPdfIframeLoad"
                  />
                  <PdfHighlightOverlay
                    :iframe-id="`pdf-viewer-${selectedDocId}`"
                    :search-results="overlayResults"
                    :active-result-index="focusedIssueId"
                    :pdf-url="pdfViewerUrl"
                    @highlight-click="onHighlightClick"
                  />
                </div>
              </div>
            </div>

            <!-- 채팅 탭 -->
            <div
              class="tab_con viewer_02"
              :class="{ on: activeTab === 'chat' }"
            >
              <div class="result_talk_wrap">
                <!-- AI 메시지 -->
                <div class="talk_ai_wrap" v-if="summary">
                  <div class="talk_doc_tit">
                    <img src="/img/icon/ic_doc.svg" alt="" />
                    <div class="txt">{{ selectedDoc?.filename }}</div>
                  </div>
                  <div class="talk_tit_01">묶음 문서 검토 결과</div>
                  <div class="talk_txt">
                    해당 계약 유형은 '<span class="fw_sb">{{
                      docTypeLabel(selectedDoc?.doc_type)
                    }}</span
                    >' 입니다.
                  </div>
                  <br />
                  <div class="talk_txt">
                    문서를 검토해 본 결과, 현재 개정된 내부 문건 규정 기준
                    <span class="ty_01 mark_box"
                      >확인 필요
                      <span class="num">{{
                        summary?.warning_issue_count || 0
                      }}</span></span
                    >
                    <span class="ty_02 mark_box"
                      >위반
                      <span class="num">{{
                        summary?.high_issue_count || 0
                      }}</span></span
                    >
                    <span class="ty_03 mark_box"
                      >누락
                      <span class="num">{{ countByCat("missing") }}</span></span
                    >
                    <span class="ty_04 mark_box"
                      >수치 오류
                      <span class="num">{{
                        countByCat("typo") + countByCat("inconsistency")
                      }}</span></span
                    >
                    건의 수정요소가 확인되었습니다.<br />
                    수정 요소는 오른쪽의 검토결과 항목을 참고하시어
                    수정해주세요.
                  </div>
                  <div class="line"></div>
                  <div class="talk_tit_02">결재선 안내</div>
                  <div v-if="approvalLine">
                    <div class="talk_txt">
                      본 계약서는 서초구청 계약 업무 처리 기준에 따라 다음과
                      같은 결재선을 통해 처리됩니다.
                    </div>
                    <div class="dot_list mt_20 mb_20 talk_txt">
                      <div
                        v-for="step in approvalLine.steps"
                        :key="step"
                        class="dot_item"
                      >
                        <span class="fw_b">{{ step }} : </span>&nbsp;{{
                          approvalRoleDesc(step)
                        }}
                      </div>
                    </div>
                    <div class="talk_txt">
                      위 결재선을 따라 순차적으로 결재를 진행해 주시기 바랍니다.
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
                    v-if="streamingText"
                    class="talk_txt"
                    v-html="streamingText.replace(/\n/g, '<br>')"
                  ></div>
                  <div
                    v-else
                    class="talk_txt"
                    style="display: flex; gap: 4px; align-items: center"
                  >
                    <span class="streaming_dot"></span>
                    <span class="streaming_dot"></span>
                    <span class="streaming_dot"></span>
                  </div>
                </div>
                <div ref="chatBottomEl"></div>
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
                  <button
                    class="search_btn"
                    aria-label="검색"
                    @click="sendChat"
                  >
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
          <!-- /tab_con_wrap -->
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
              <!-- 검토 전/결과 없음 -->
              <div v-if="!currentDocIssues.length" class="empty_wrap">
                <div class="ic_wrap">
                  <img src="/img/icon/ic_empty_result.svg" alt="" />
                </div>
                <div class="txt_wrap">
                  검토결과 출력이 여기에 저장됩니다.<br />
                  소스를 추가한 후 클릭하여 내용을 확인하세요.
                </div>
              </div>
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

    <!-- 로딩 오버레이 -->
    <div class="review_loading" v-if="false">
      <span class="review_spin"
        ><img src="/img/icon/ic_loading.svg" alt=""
      /></span>
      <p class="review_txt">문서 검토중...</p>
    </div>

    <!-- ── 체크리스트 팝업 (컴포넌트) -->
    <ChecklistPopup
      v-model="showChecklist"
      :review-run-id="runId"
      :ai-errors="checklistAiErrors"
      @saved="onChecklistSaved"
    />

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
const checklistAiErrors = ref<Record<string, string>>({});

// 채팅
const chatHistory = ref<{ role: string; content: string }[]>([]);
const chatInput = ref("");
const isStreaming = ref(false);
const streamingText = ref("");
const chatBottomEl = ref<HTMLElement>();

// PDF 뷰어
const viewerEl = ref<HTMLElement>();
const currentPage = ref(1);
const totalPage = ref(1);
const hoveredIssueId = ref<number | null>(null);
const focusedIssueId = ref<number | null>(null);

const reportDownloadUrl = computed(() => getReportDownloadUrl(runId.value));

// PDF.js viewer URL — /pdfjs/web/viewer.html?file={PDF API URL}
const pdfViewerUrl = computed(() => {
  if (!selectedDoc.value) return "";
  const pdfUrl = encodeURIComponent(
    `/api/v1/projects/1/reviews/${runId.value}/pdf/${selectedDoc.value.document_id}`,
  );
  return `/pdfjs/web/viewer.html?file=${pdfUrl}`;
});

// 하이라이트를 PdfHighlightOverlay 포맷으로 변환
const overlayResults = computed(() =>
  currentDocIssues.value
    .filter((iss) => iss.highlights?.length)
    .map((iss) => ({
      score:
        iss.severity === "critical"
          ? 0.95
          : iss.severity === "high"
            ? 0.8
            : 0.6,
      bbox_info: iss.highlights.map((h: any) => ({
        page: h.page_no,
        x0: h.bbox?.x1 ?? 0,
        y0: h.bbox?.y1 ?? 0,
        x1: h.bbox?.x2 ?? 0,
        y1: h.bbox?.y2 ?? 0,
      })),
      article_bbox_info: [],
      display_path: iss.title,
      korean_text: iss.description,
      _issue_id: iss.id,
    })),
);

// ── 문서 카테고리 그룹핑
const docGroups = computed(() => {
  const groups: Record<string, { label: string; open: boolean; files: any[] }> =
    {};
  for (const f of docFiles.value) {
    const label = docTypeLabel(f.doc_type);
    if (!groups[label]) groups[label] = { label, open: true, files: [] };
    groups[label].files.push(f);
  }
  return Object.values(groups);
});

function fileIcon(filename: string) {
  const ext = filename.split(".").pop()?.toLowerCase() || "";
  const map: Record<string, string> = {
    pdf: "/img/icon/ic_file_pdf.svg",
    hwp: "/img/icon/ic_file_hwp.svg",
    hwpx: "/img/icon/ic_file_hwpx.svg",
    xlsx: "/img/icon/ic_file_xlsx.svg",
    xls: "/img/icon/ic_file_xlsx.svg",
    txt: "/img/icon/ic_file_txt.svg",
  };
  return map[ext] || "/img/icon/ic_doc.svg";
}

function removeDoc(docId: number) {
  docFiles.value = docFiles.value.filter((f) => f.document_id !== docId);
  if (selectedDoc.value?.document_id === docId) {
    selectedDoc.value = docFiles.value[0] || null;
    if (selectedDoc.value) selectDoc(selectedDoc.value);
  }
}

// ── 현재 문서 이슈
const currentDocIssues = computed(() =>
  selectedDocId.value
    ? issues.value.filter((i) => i.document_id === selectedDocId.value)
    : issues.value,
);

// ── 현재 페이지 하이라이트

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
  // PDF는 pdfViewerUrl computed가 자동으로 iframe src 갱신
}

function onPdfIframeLoad() {
  // iframe 로드 완료 — PdfHighlightOverlay가 자동으로 연결
  console.log("[PDF] iframe 로드 완료");
}

function goToPage(pageNum: number) {
  if (pageNum < 1) return;
  currentPage.value = pageNum;
  // PDF.js iframe 내부 페이지 이동
  const iframe = document.getElementById(
    `pdf-viewer-${selectedDocId.value}`,
  ) as HTMLIFrameElement;
  if (iframe?.contentWindow) {
    try {
      const pdfApp = (iframe.contentWindow as any).PDFViewerApplication;
      if (pdfApp?.page !== undefined) pdfApp.page = pageNum;
    } catch (e) {
      console.warn("[PDF] 페이지 이동 실패", e);
    }
  }
}

function onIssueClick(iss: any) {
  focusedIssueId.value = iss.id;
  activeTab.value = "doc";
  const hl = highlights.value.find((h) => h.issue_id === iss.id);
  if (hl?.page_no) goToPage(hl.page_no);
}

function onHighlightClick(_result: any, _rectInfo: any) {
  // 하이라이트 클릭 → 우측 이슈카드 포커스
  const issueId = _result._issue_id;
  if (issueId) focusedIssueId.value = issueId;
}

async function loadChecklist() {
  try {
    const res = await getChecklist(runId.value);
    const items = (res as any).data?.items || [];
    checklistItems.value = items;
    // AI 오류 항목 추출 (result === 'fail' 인 것)
    const errors: Record<string, string> = {};
    items.forEach((item: any, i: number) => {
      if (item.result === "fail")
        errors[`q${i + 1}`] = item.comment || item.title;
    });
    checklistAiErrors.value = errors;
  } catch {}
}

function onChecklistSaved(selections: Record<string, string>) {
  console.log("[체크리스트] 저장됨", selections);
}

// ── 채팅
async function sendChat() {
  const q = chatInput.value.trim();
  if (!q || isStreaming.value) return;
  chatInput.value = "";
  chatHistory.value.push({ role: "user", content: q });
  isStreaming.value = true;
  streamingText.value = "";

  const scrollToBottom = () => {
    nextTick(() => chatBottomEl.value?.scrollIntoView({ behavior: "smooth" }));
  };

  chatStream(
    q,
    runId.value,
    selectedDocId.value || 0,
    (chunk) => {
      streamingText.value += chunk;
      scrollToBottom();
    },
    () => {
      chatHistory.value.push({
        role: "assistant",
        content: streamingText.value,
      });
      streamingText.value = "";
      isStreaming.value = false;
      scrollToBottom();
    },
    (err) => {
      chatHistory.value.push({
        role: "assistant",
        content: `오류가 발생했습니다: ${err}`,
      });
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

function countBySev(sev: string) {
  return currentDocIssues.value.filter((i) => i.severity === sev).length;
}
function countByCat(cat: string) {
  return currentDocIssues.value.filter((i) => i.category === cat).length;
}

function approvalRoleDesc(step: string) {
  const map: Record<string, string> = {
    담당: "계약 내용 작성 및 1차 검토",
    팀장: "부서 내 검토 및 보완 지시",
    과장: "부서 책임자 검토",
    국장: "국 단위 정책·예산 적정성 검토",
    부구청장: "주요 사항 승인",
    구청장: "최종 승인",
  };
  return map[step] || "";
}

function closeTrigger(id: string) {
  const wrap = document.getElementById(id + "_wrap");
  const toggle = document.getElementById(id + "_toggle");
  const el = document.getElementById(id);
  if (wrap) wrap.classList.remove("open");
  if (toggle) toggle.classList.remove("open");
  if (el) el.classList.remove("open");
}

function logout() {
  localStorage.removeItem("clms_logged_in");
  route.push("/");
}
</script>
