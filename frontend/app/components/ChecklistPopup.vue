<template>
  <div class="dim" :class="{ open: modelValue }">
    <div
      class="layer_popup pop_checklist"
      id="pop_checklist"
      role="dialog"
      aria-modal="true"
    >
      <button
        type="button"
        class="ic_close pop_close"
        aria-label="팝업 닫기"
        @click="$emit('update:modelValue', false)"
      ></button>
      <div class="popup_header">체크리스트</div>
      <div class="popup_body">
        <div class="checklist_txt">
          목표 달성에 도움이 되도록 맞춤설정 할 수 있습니다.
        </div>

        <!-- 전체 결과 요약 -->
        <div class="checklist_info" :class="{ error: hasError }">
          <div class="checklist_info_ic"></div>
          <div class="checklist_info_txt">
            <div class="tit">{{ hasError ? "항목 미충족" : "항목 충족" }}</div>
            <div class="txt">
              {{
                hasError ? errorSummary : "모든 항목이 적합하게 작성되었습니다."
              }}
            </div>
          </div>
        </div>

        <div class="checklist_wrap">
          <!-- 질문 1: 계약 목적물 분류 -->
          <div class="checklist_item">
            <div class="checklist_item_tit">
              1. 계약목적물 분류상 어떤 계약인가?
            </div>
            <div v-if="props.aiErrors?.['q1']" class="checklist_item_txt error">
              {{ props.aiErrors?.["q1"] }}
            </div>
            <div class="form_check_wrap">
              <div
                v-for="opt in q1Options"
                :key="opt.value"
                class="form_check ty_01"
                :class="{ error: opt.isError }"
              >
                <input
                  type="checkbox"
                  :id="`chk_01_${opt.value}`"
                  :checked="selections.q1 === opt.value"
                  @change="setSelection('q1', opt.value)"
                />
                <label :for="`chk_01_${opt.value}`">{{ opt.label }}</label>
              </div>
            </div>
          </div>

          <!-- 질문 2: 구체적 계약 유형 -->
          <div class="checklist_item">
            <div class="checklist_item_tit">2. 구체적으로 어떤 계약인지?</div>
            <div class="checklist_item_txt">
              *용역 및 물품계약의 경우 1천만원 이상 중소기업자간 경쟁제품에
              해당된다면<br />
              "직접생산확인서" 확인 必
            </div>
            <div class="list check_ty_01">
              <div v-for="group in q2Groups" :key="group.value" class="item">
                <div class="form_check ty_01">
                  <input
                    type="checkbox"
                    :id="`chk_02_${group.value}`"
                    :checked="selections.q2_group === group.value"
                    @change="
                      setSelection('q2_group', group.value);
                      selections.q2_detail = '';
                    "
                  />
                  <label :for="`chk_02_${group.value}`">{{
                    group.label
                  }}</label>
                </div>
                <div class="choice_list">
                  <a
                    v-for="detail in group.details"
                    :key="detail.value"
                    href="#;"
                    class="choice_item"
                    :class="{
                      on:
                        selections.q2_group === group.value &&
                        selections.q2_detail === detail.value,
                      error: detail.isError,
                    }"
                    @click.prevent="
                      setSelection('q2_group', group.value);
                      setSelection('q2_detail', detail.value);
                    "
                  >
                    {{ detail.label }}
                  </a>
                </div>
              </div>
            </div>
          </div>

          <!-- 질문 3: 소요예산 계약 방법 -->
          <div class="checklist_item">
            <div class="checklist_item_tit">
              3. 사업 소요예산에 가능한 계약은?
            </div>
            <div class="list check_ty_02">
              <div v-for="opt in q3Options" :key="opt.value" class="item">
                <div class="form_check ty_01">
                  <input
                    type="checkbox"
                    :id="`chk_03_${opt.value}`"
                    :checked="selections.q3 === opt.value"
                    @change="
                      setSelection('q3', opt.value);
                      selections.q3_detail = '';
                    "
                  />
                  <label :for="`chk_03_${opt.value}`">{{ opt.label }}</label>
                </div>
                <div v-if="opt.details" class="choice_list">
                  <a
                    v-for="d in opt.details"
                    :key="d"
                    href="#;"
                    class="choice_item"
                    :class="{
                      on:
                        selections.q3 === opt.value &&
                        selections.q3_detail === d,
                    }"
                    @click.prevent="
                      setSelection('q3', opt.value);
                      setSelection('q3_detail', d);
                    "
                  >
                    {{ d }}
                  </a>
                </div>
              </div>
            </div>
          </div>

          <!-- 질문 4: 경쟁 형태 -->
          <div class="checklist_item">
            <div class="checklist_item_tit">
              4. 경쟁형태를 어떻게 결정할 것인지?
            </div>
            <div class="list check_ty_03">
              <div v-for="opt in q4Options" :key="opt.value" class="item">
                <div class="form_check ty_01">
                  <input
                    type="checkbox"
                    :id="`chk_04_${opt.value}`"
                    :checked="selections.q4 === opt.value"
                    @change="
                      setSelection('q4', opt.value);
                      selections.q4_detail = '';
                    "
                  />
                  <label :for="`chk_04_${opt.value}`">{{ opt.label }}</label>
                </div>
                <div v-if="opt.details" class="choice_list">
                  <a
                    v-for="d in opt.details"
                    :key="d"
                    href="#;"
                    class="choice_item"
                    :class="{
                      on:
                        selections.q4 === opt.value &&
                        selections.q4_detail === d,
                    }"
                    @click.prevent="
                      setSelection('q4', opt.value);
                      setSelection('q4_detail', d);
                    "
                  >
                    {{ d }}
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="popup_footer">
        <button type="button" class="btn sz_r btn_ty02" @click="save">
          저장
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: boolean;
    reviewRunId: number;
    aiErrors?: Record<string, string>;
  }>(),
  {
    aiErrors: () => ({}),
  },
);

const emit = defineEmits(["update:modelValue", "saved"]);

const { saveChecklistForm } = useApi();

// ── 선택값 상태
const selections = reactive<Record<string, string>>({
  q1: "",
  q2_group: "",
  q2_detail: "",
  q3: "",
  q3_detail: "",
  q4: "",
  q4_detail: "",
});

// ── 질문 옵션 정의
const q1Options = computed(() => [
  { value: "construction", label: "공사", isError: !!props.aiErrors?.["q1"] },
  { value: "service", label: "용역", isError: false },
  { value: "goods", label: "물품", isError: false },
]);

const q2Groups = [
  {
    value: "construction",
    label: "공사 계약",
    details: [
      {
        value: "general",
        label: "종합",
        isError: props.aiErrors?.["q2"] === "general",
      },
      { value: "special", label: "전문", isError: false },
      { value: "electric", label: "전기", isError: false },
      { value: "it", label: "정보통신", isError: false },
      { value: "fire", label: "소방", isError: false },
    ],
  },
  {
    value: "service",
    label: "용역 계약",
    details: [
      { value: "general", label: "일반", isError: false },
      { value: "technical", label: "기술", isError: false },
      { value: "research", label: "학습", isError: false },
    ],
  },
  {
    value: "goods",
    label: "물품 계약",
    details: [
      { value: "manufacture", label: "제조구매", isError: false },
      { value: "purchase", label: "구매", isError: false },
    ],
  },
];

const q3Options = [
  {
    value: "single_quote",
    label: "1인견적 수의계약이 가능한지",
    details: ["추정가격 2천만원 이하", "추정가격 5천만원 이하"],
  },
  {
    value: "double_quote",
    label: "2인견적 수의계약(전자공개)이 가능한지",
    details: [
      "종합공사 4억 이하",
      "전문공사 2억 이하",
      "전기, 통신 등 기타공사 1억6천 이하",
      "용역·물품 1억 이하",
    ],
  },
  {
    value: "open_bid",
    label: "공개경쟁입찰로 진행할 것인지",
    details: undefined,
  },
];

const q4Options = [
  {
    value: "negotiated",
    label: "수의계약",
    details: ["1인견적", "2인견적 (전자공개)"],
  },
  {
    value: "competitive",
    label: "경쟁계약입찰",
    details: [
      "일반경쟁계약",
      "지명경쟁계약",
      "제한경쟁계약(지역제한, 실적제한 등)",
    ],
  },
];

// ── 오류 여부
const hasError = computed(() => Object.keys(props.aiErrors ?? {}).length > 0);
const errorSummary = computed(() => {
  const errs = props.aiErrors ?? {};
  if (errs.q1) return errs.q1;
  return Object.values(errs)[0] || "";
});

function setSelection(key: string, value: string) {
  selections[key] = selections[key] === value ? "" : value;
}

async function save() {
  try {
    await saveChecklistForm(props.reviewRunId, { ...selections });
    emit("saved", { ...selections });
  } catch (e) {
    console.error("체크리스트 저장 실패", e);
  } finally {
    emit("update:modelValue", false);
  }
}
</script>
