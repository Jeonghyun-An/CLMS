<template>
  <div class="login_wrap" id="login_wrap">
    <div class="login_box">
      <div class="login_box_inn">
        <div class="login_logo">
          <img
            src="/img/layout/hd_logo.svg"
            alt="오늘 행복하고 내일이 기다려지는 서초"
          />
        </div>
        <div class="login_tit">로그인</div>
        <div class="login_input_wrap">
          <div class="login_id" :class="{ error: errorMsg }">
            <label class="login_input_tit" for="input_id">아이디</label>
            <div class="login_input_box">
              <input
                v-model="form.id"
                type="text"
                id="input_id"
                class="login_input"
                placeholder="아이디를 입력해주세요."
                @keyup.enter="login"
              />
            </div>
          </div>
          <div class="login_pw" :class="{ error: errorMsg }">
            <label class="login_input_tit" for="input_pw">비밀번호</label>
            <div class="login_input_box">
              <input
                v-model="form.pw"
                :type="showPw ? 'text' : 'password'"
                id="input_pw"
                class="login_input"
                placeholder="비밀번호를 입력해주세요."
                @keyup.enter="login"
              />
              <button
                type="button"
                class="view_pw"
                :class="{ on: showPw }"
                @click="showPw = !showPw"
              ></button>
            </div>
          </div>
          <div v-if="errorMsg" class="error_msg">
            <img src="/img/icon/ic_error.svg" alt="" />
            {{ errorMsg }}
          </div>
        </div>
        <button
          type="button"
          class="btn sz_lg sq btn_ty05 login_btn"
          @click="login"
        >
          로그인
        </button>
        <div class="login_util_wrap">
          <div class="form_check ty_02 remember_id">
            <input type="checkbox" id="chk_02" v-model="rememberId" />
            <label for="chk_02">아이디 저장</label>
          </div>
          <div class="login_util_list">
            <span class="login_util_item"><a href="#;">아이디 찾기</a></span>
            <span class="login_util_item"><a href="#;">비밀번호 찾기</a></span>
            <span class="login_util_item"><a href="#;">회원가입</a></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const POC_ID = "seocho";
const POC_PW = "1234";

const form = reactive({ id: "", pw: "" });
const showPw = ref(false);
const rememberId = ref(false);
const errorMsg = ref("");
const router = useRouter();

onMounted(() => {
  const saved = localStorage.getItem("clms_saved_id");
  if (saved) {
    form.id = saved;
    rememberId.value = true;
  }
  if (localStorage.getItem("clms_logged_in")) router.push("/main");
});

function login() {
  errorMsg.value = "";
  if (!form.id || !form.pw) {
    errorMsg.value = "아이디와 비밀번호를 입력해주세요.";
    return;
  }
  if (form.id !== POC_ID || form.pw !== POC_PW) {
    errorMsg.value = "아이디 또는 비밀번호가 올바르지 않습니다.";
    return;
  }
  if (rememberId.value) localStorage.setItem("clms_saved_id", form.id);
  else localStorage.removeItem("clms_saved_id");
  localStorage.setItem("clms_logged_in", "1");
  router.push("/main");
}
</script>
