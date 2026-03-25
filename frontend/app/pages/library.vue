<template>
  <div class="contents_wrap" id="contents_wrap">
    <ul class="skip_menu">
      <li><a href="#contents_wrap">컨텐츠 바로가기</a></li>
    </ul>

    <!-- 헤더 -->
    <div class="header">
      <div class="left">
        <a href="/main" class="hd_logo">
          <img
            src="/img/layout/hd_logo.svg"
            alt="오늘 행복하고 내일이 기다려지는 서초"
          />
        </a>
      </div>
      <div class="right">
        <a href="/main" class="btn sz_s btn_ty05">
          <img src="/img/icon/ic_plus_w.svg" alt="" />신규
        </a>
        <a href="#;" class="btn sz_s btn_ty04">
          <img src="/img/icon/ic_admin.svg" alt="" class="ic_color" />관리자
        </a>
        <a href="#;" class="btn sz_s hover_bg_01 btn_menu">
          <img src="/img/icon/ic_menu.svg" aria-label="메뉴" alt="" />
        </a>
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

    <!-- 콘텐츠 -->
    <div class="contents_inn">
      <div class="library_wrap contents_inn_box">
        <div class="inner">
          <!-- 상단 툴바 -->
          <div class="library_top">
            <div class="select_box">
              <select v-model="sortOrder">
                <option value="latest">최신순</option>
                <option value="oldest">과거순</option>
                <option value="asc">오름차순</option>
                <option value="desc">내림차순</option>
              </select>
            </div>
            <div class="search_wrap_area" :class="{ on: searchOpen }">
              <div class="search_dim" @click="searchOpen = false"></div>
              <div class="search_wrap">
                <input
                  v-model="searchKeyword"
                  type="text"
                  class="search_input"
                  aria-label="검색어 입력"
                  @keyup.enter="doSearch"
                />
                <button
                  class="search_btn"
                  aria-label="검색"
                  @click="
                    searchOpen = true;
                    doSearch();
                  "
                >
                  <img src="/img/icon/ic_btn_search.svg" alt="" />
                </button>
              </div>
            </div>
            <!-- 뷰 전환 -->
            <ul class="list_ty">
              <li
                class="list_ty_item ty_thumb"
                :class="{ on: viewType === 'thumb' }"
              >
                <a href="#;" @click.prevent="viewType = 'thumb'">
                  <img src="/img/icon/ic_thumb.svg" alt="" />
                </a>
              </li>
              <li
                class="list_ty_item ty_list"
                :class="{ on: viewType === 'list' }"
              >
                <a href="#;" @click.prevent="viewType = 'list'">
                  <img src="/img/icon/ic_list.svg" alt="" />
                </a>
              </li>
            </ul>
          </div>

          <!-- ── 썸네일 뷰 -->
          <div v-if="viewType === 'thumb'" class="library_list">
            <!-- 새 노트 만들기 -->
            <a href="/main" class="new_note">
              <div class="new_note_inn">
                <span class="ic"
                  ><img src="/img/icon/ic_plus.svg" alt=""
                /></span>
                <div class="txt">새 노트 만들기</div>
              </div>
            </a>
            <!-- 프로젝트 카드 -->
            <div
              v-for="(item, i) in filteredProjects"
              :key="item.id"
              class="library_item"
              :class="`ty_0${(i % 5) + 1}`"
            >
              <a :href="`/main`" class="library_item_inn">
                <div class="item_menu_wrap">
                  <img :src="`/img/icon/ic_note_0${(i % 5) + 1}.svg`" alt="" />
                </div>
                <div class="item_tit_wrap">
                  <span>{{ item.name }}</span>
                  <span class="source">소스 {{ item.document_count }}개</span>
                </div>
                <div class="item_info_wrap">
                  <div class="left">
                    <div class="date">{{ formatDate(item.created_at) }}</div>
                    <div class="admin">관리자 : 서초구청</div>
                  </div>
                  <div class="right">
                    <div class="profile">
                      <img src="/img/layout/img_profile_01.svg" alt="" />
                    </div>
                    <div class="member">3+</div>
                  </div>
                </div>
              </a>
              <a href="#;" class="item_menu" aria-label="메뉴"></a>
            </div>
          </div>

          <!-- ── 리스트 뷰 -->
          <div v-else class="library_list_list">
            <table class="table ty_01">
              <caption>
                라이브러리 목록 - 프로젝트명, 문서, 생성됨, 관리자, 공유된
                멤버로 구성
              </caption>
              <colgroup>
                <col />
                <col class="w_15p" />
                <col class="w_15p" />
                <col class="w_15p" />
                <col class="w_15p" />
              </colgroup>
              <thead>
                <tr>
                  <th class="tit">프로젝트명</th>
                  <th>문서</th>
                  <th>생성됨</th>
                  <th>관리자</th>
                  <th>공유된 멤버</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, i) in filteredProjects" :key="item.id">
                  <td>
                    <a :href="`/main`" class="ellipsis tit">
                      <img
                        :src="`/img/icon/ic_note_0${(i % 5) + 1}.svg`"
                        alt=""
                      />
                      {{ item.name }}
                    </a>
                  </td>
                  <td>소스 {{ item.document_count }}개</td>
                  <td>{{ formatDate(item.created_at) }}</td>
                  <td>서초구청</td>
                  <td>3인</td>
                </tr>
                <!-- 데이터 없을 때 -->
                <tr v-if="!filteredProjects.length">
                  <td
                    colspan="5"
                    style="text-align: center; padding: 40px; color: #aaa"
                  >
                    프로젝트가 없습니다.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const router = useRouter();
const { createProject } = useApi();

const viewType = ref<"thumb" | "list">("thumb");
const sortOrder = ref("latest");
const searchKeyword = ref("");
const searchOpen = ref(false);
const projects = ref<any[]>([]);

// 샘플 데이터 (API 연동 전)
const SAMPLE_PROJECTS = Array.from({ length: 10 }, (_, i) => ({
  id: i + 1,
  name: `서초구청 AI 계약검토 프로젝트 ${i + 1}`,
  document_count: Math.floor(Math.random() * 5) + 1,
  created_at: new Date(Date.now() - i * 86400000 * 3).toISOString(),
}));

onMounted(() => {
  if (!localStorage.getItem("clms_logged_in")) {
    router.push("/");
    return;
  }
  document.addEventListener("click", handleTrigger);
  loadProjects();
});
onUnmounted(() => document.removeEventListener("click", handleTrigger));

async function loadProjects() {
  try {
    const res = (await $fetch("/api/v1/projects")) as any;
    projects.value = res.data?.items || SAMPLE_PROJECTS;
  } catch {
    projects.value = SAMPLE_PROJECTS;
  }
}

const filteredProjects = computed(() => {
  let list = [...projects.value];
  if (searchKeyword.value) {
    list = list.filter((p) => p.name.includes(searchKeyword.value));
  }
  if (sortOrder.value === "latest")
    list.sort((a, b) => (b.created_at > a.created_at ? 1 : -1));
  if (sortOrder.value === "oldest")
    list.sort((a, b) => (a.created_at > b.created_at ? 1 : -1));
  if (sortOrder.value === "asc")
    list.sort((a, b) => a.name.localeCompare(b.name));
  if (sortOrder.value === "desc")
    list.sort((a, b) => b.name.localeCompare(a.name));
  return list;
});

function doSearch() {
  searchOpen.value = false;
}

function formatDate(iso: string) {
  if (!iso) return "";
  return new Date(iso)
    .toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    })
    .replace(/\. /g, ".")
    .replace(/\.$/, "");
}

function handleTrigger(e: MouseEvent) {
  const el = (e.target as HTMLElement).closest(
    ".trigger",
  ) as HTMLElement | null;
  if (!el) return;
  const id = el.getAttribute("id");
  if (!id) return;
  const wrap = document.getElementById(id + "_wrap");
  const toggle = document.getElementById(id + "_toggle");
  const header = el.closest(".header");
  if (header) {
    header.querySelectorAll(".trigger").forEach((t: any) => {
      if (t === el) return;
      const tid = t.getAttribute("id");
      if (!tid) return;
      document.getElementById(tid + "_wrap")?.classList.remove("open");
      document.getElementById(tid + "_toggle")?.classList.remove("open");
      t.classList.remove("open");
    });
  }
  wrap?.classList.toggle("open");
  toggle?.classList.toggle("open");
  el.classList.toggle("open");
}

function closeTrigger(id: string) {
  document.getElementById(id + "_wrap")?.classList.remove("open");
  document.getElementById(id + "_toggle")?.classList.remove("open");
  document.getElementById(id)?.classList.remove("open");
}

function logout() {
  localStorage.removeItem("clms_logged_in");
  router.push("/");
}
</script>
