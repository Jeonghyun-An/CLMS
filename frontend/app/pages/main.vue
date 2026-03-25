<template>
  <div class="contents_wrap" id="contents_wrap">
    <ul class="skip_menu">
      <li><a href="#contents_wrap">본문 바로가기</a></li>
    </ul>
    <!-- 헤더 -->
    <div class="header">
      <div class="left">
        <div class="pj_tit_wrap" :class="{ is_edit: isEditTitle }">
          <a href="#;" class="pj_img"
            ><img src="/img/layout/img_pj.svg" alt=""
          /></a>
          <span class="pj_tit txt">{{ projectTitle }}</span>
          <input
            type="text"
            v-model="projectTitle"
            class="pj_tit edit"
            :disabled="!isEditTitle"
          />
          <button
            class="btn_edit"
            aria-label="타이틀 수정"
            @click="toggleEditTitle"
          ></button>
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

        <!-- 신규 버튼 -->
        <a href="#;" class="btn sz_s btn_ty05" @click.prevent="goReview">
          <img src="/img/icon/ic_plus_w.svg" alt="" />신규
        </a>

        <!-- 관리자 버튼 -->
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
                aria-label="공유 닫기"
                class="share_trigger_close trigger_close"
                data-target="share_trigger"
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
                v-for="(m, i) in shareMembers"
                :key="i"
                class="share_trigger_item"
              >
                <div class="share_trigger_item_inn">
                  <a href="#;" class="name_wrap">
                    <div class="img_wrap">
                      <img
                        :src="`/img/layout/img_profile_0${(i % 3) + 1}.svg`"
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

        <!-- 메뉴 버튼 -->
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
      <!-- 좌측 패널: 문서 목록 -->
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
            <a href="#;" class="icon">
              <img src="/img/icon/ic_panel_plus.svg" alt="" />
            </a>
          </div>
          <div class="btm">
            <a
              href="#;"
              class="icon btn_review_start"
              @click.prevent="startReview"
            >
              <img src="/img/icon/ic_panel_start.svg" alt="" />
            </a>
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
            <label
              class="btn sz_md sq btn_ty02 btn_full"
              style="cursor: pointer"
            >
              <img src="/img/icon/ic_plus_p.svg" alt="" /> 소스 추가
              <input
                type="file"
                multiple
                accept=".pdf,.hwp,.hwpx,.xlsx"
                class="file_upload_input"
                style="display: none"
                @change="onFileChange"
              />
            </label>
          </div>
          <div class="source_list_wrap">
            <div class="source_list">
              <div
                v-if="!selectedFiles.length"
                class="empty_wrap"
                style="padding: 20px; text-align: center"
              >
                <div class="ic_wrap">
                  <img src="/img/icon/ic_empty_source.svg" alt="" />
                </div>
                <div class="txt_wrap">
                  저장된 소스가 여기에 표시됩니다.<br />(pdf, hwpx, xlsx 가능)
                </div>
              </div>
              <div v-else class="accordion">
                <div
                  v-for="(f, i) in selectedFiles"
                  :key="i"
                  class="accordion_panel_item on"
                >
                  <div
                    class="panel_item_tit_wrap"
                    style="
                      display: flex;
                      align-items: center;
                      gap: 8px;
                      padding: 8px 12px;
                    "
                  >
                    <img
                      src="/img/icon/ic_doc.svg"
                      alt=""
                      style="width: 16px"
                    />
                    <span class="ellipsis" style="flex: 1; font-size: 13px">{{
                      f.name
                    }}</span>
                    <a href="#;" class="ic_del" @click.prevent="removeFile(i)">
                      <img
                        src="/img/icon/ic_close.svg"
                        alt=""
                        style="width: 12px"
                      />
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="panel_btm">
            <button
              type="button"
              class="btn sz_md sq btn_ty05 btn_full"
              :disabled="!selectedFiles.length || isLoading"
              @click="startReview"
            >
              검토 시작
            </button>
          </div>
        </div>
      </div>

      <!-- 가운데: 업로드 영역 -->
      <div class="contents_inn_box center_box main_box">
        <div class="main_box_inn">
          <div class="main_logo">
            <img
              src="/img/layout/hd_logo.svg"
              alt="오늘 행복하고 내일이 기다려지는 서초"
            />
          </div>
          <div class="main_txt">
            <span class="gradient_txt">사용자의 문서</span>를 활용해 AI 개정이력
            및<br />
            리포트 문서 뷰어 검토·관리하기
          </div>
          <div
            class="upload_wrap"
            :class="{ is_upload: selectedFiles.length, dragover: isDragging }"
            @dragenter.prevent="isDragging = true"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="onDrop"
          >
            <div class="upload_tit_wrap">
              <template v-if="!selectedFiles.length">
                <p class="upload_tit">또는 파일 드롭</p>
                <p class="upload_desc">PDF, hwpx, xlsx 등</p>
              </template>
              <ul v-else class="upload_file_list">
                <li v-for="(f, i) in selectedFiles" :key="i">{{ f.name }}</li>
              </ul>
            </div>
            <input
              type="file"
              multiple
              accept=".pdf,.hwp,.hwpx,.xlsx"
              class="file_upload_input"
              ref="fileInputMain"
              @change="onFileChange"
              style="display: none"
            />
            <div class="upload_btns">
              <button
                type="button"
                class="upload_btn btn sz_r btn_ty04"
                @click="fileInputMain?.click()"
              >
                <img src="/img/icon/ic_upload.svg" alt="" />파일업로드
              </button>
            </div>
          </div>
        </div>
        <div class="alert_txt">
          <img src="/img/icon/ic_alert.svg" alt="" />
          Ai가 부정확한 정보를 표시할 수 있으므로 대답을 다시 한번 확인하세요.
        </div>
      </div>

      <!-- 우측 패널: 빈 결과 -->
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
          <div class="result_list_wrap">
            <div class="result_list">
              <div class="empty_wrap">
                <div class="ic_wrap">
                  <img src="/img/icon/ic_empty_result.svg" alt="" />
                </div>
                <div class="txt_wrap">
                  검토결과 출력이 여기에 저장됩니다.<br />
                  소스를 추가한 후 클릭하여 내용을 확인하세요.
                </div>
              </div>
            </div>
          </div>
          <div class="panel_btm">
            <a href="#;" class="btn sz_md sq btn_ty02 btn_full">
              <img src="/img/icon/ic_check_p.svg" alt="" />체크리스트
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- 로딩 오버레이 -->
    <div class="review_loading" :hidden="!isLoading">
      <span class="review_spin"
        ><img src="/img/icon/ic_loading.svg" alt=""
      /></span>
      <p class="review_txt">{{ loadingText }}</p>
      <div v-if="loadingProgress > 0" class="review_progress">
        <div
          class="review_progress_bar"
          :style="{ width: loadingProgress * 100 + '%' }"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const router = useRouter();
const { uploadStream } = useApi();

const projectTitle = ref("AI 계약서류 검토");
const isEditTitle = ref(false);
const leftOpen = ref(true);
const rightOpen = ref(true);
const selectedFiles = ref<File[]>([]);
const isDragging = ref(false);
const isLoading = ref(false);
const loadingText = ref("문서 검토중...");
const loadingProgress = ref(0);
const fileInputMain = ref<HTMLInputElement>();

const shareMembers = ref([
  { name: "누구나" },
  { name: "최승환" },
  { name: "홍길동" },
]);

function closeTrigger(id: string) {
  const wrap = document.getElementById(id + "_wrap");
  const toggle = document.getElementById(id + "_toggle");
  const el = document.getElementById(id);
  if (wrap) wrap.classList.remove("open");
  if (toggle) toggle.classList.remove("open");
  if (el) el.classList.remove("open");
}

onMounted(() => {
  if (!localStorage.getItem("clms_logged_in")) router.push("/");
  // 트리거 토글 (퍼블리싱 JS 로직)
  document.addEventListener("click", handleTrigger);
});
onUnmounted(() => document.removeEventListener("click", handleTrigger));

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

function toggleEditTitle() {
  isEditTitle.value = !isEditTitle.value;
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement;
  if (!input.files) return;
  addFiles(Array.from(input.files));
}

function onDrop(e: DragEvent) {
  isDragging.value = false;
  if (!e.dataTransfer?.files) return;
  addFiles(Array.from(e.dataTransfer.files));
}

function addFiles(files: File[]) {
  const existing = new Set(selectedFiles.value.map((f) => f.name));
  for (const f of files) {
    if (!existing.has(f.name)) selectedFiles.value.push(f);
  }
}

function removeFile(i: number) {
  selectedFiles.value.splice(i, 1);
}

async function startReview() {
  if (!selectedFiles.value.length) return;
  isLoading.value = true;
  loadingProgress.value = 0;
  loadingText.value = "문서 검토중...";

  try {
    const runId = await uploadStream(selectedFiles.value, true, (evt) => {
      if (evt.type === "file_start")
        loadingText.value = `${evt.filename} OCR 중...`;
      if (evt.type === "ocr_page") loadingProgress.value = evt.progress;
      if (evt.type === "review_start") loadingText.value = "검토 분석 중...";
      if (evt.type === "file_done")
        loadingText.value = `${evt.filename} 완료 (이슈 ${evt.issue_count}건)`;
    });
    router.push(`/review/${runId}`);
  } catch (e) {
    alert("검토 중 오류가 발생했습니다.");
  } finally {
    isLoading.value = false;
  }
}

function goReview() {
  selectedFiles.value = [];
  leftOpen.value = true;
}

function logout() {
  localStorage.removeItem("clms_logged_in");
  router.push("/");
}
</script>
