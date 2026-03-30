<template>
  <div class="pdf-overlay-root">
    <div
      v-for="(rect, idx) in flatRects"
      :key="rect.key"
      class="pdf-overlay-rect"
      :class="{
        active: activeIssueId != null && rect.issueId === activeIssueId,
      }"
      :style="{
        left: `${rect.left}px`,
        top: `${rect.top}px`,
        width: `${rect.width}px`,
        height: `${rect.height}px`,
      }"
      :title="rect.text || rect.section || ''"
      @click.stop="handleClick(rect, idx)"
    />
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";

type RectInfo = {
  key: string;
  issueId: number | null;
  page: number;
  left: number;
  top: number;
  width: number;
  height: number;
  text?: string;
  section?: string;
  rawResult: any;
  rawRect: any;
};

const props = defineProps<{
  iframeId: string;
  searchResults: any[];
  activeResultIndex?: number | null;
  pdfUrl?: string;
}>();

const emit = defineEmits<{
  (e: "highlight-click", result: any, rectInfo: any): void;
}>();

const flatRects = ref<RectInfo[]>([]);
const activeIssueId = computed(() => props.activeResultIndex ?? null);

let redrawTimer: number | null = null;
let observeTimer: number | null = null;
let resizeHandler: (() => void) | null = null;

function getIframe(): HTMLIFrameElement | null {
  return document.getElementById(props.iframeId) as HTMLIFrameElement | null;
}

function getIframeDocument(): Document | null {
  const iframe = getIframe();
  try {
    return iframe?.contentDocument || iframe?.contentWindow?.document || null;
  } catch {
    return null;
  }
}

function scheduleRedraw(delay = 0) {
  if (redrawTimer) {
    window.clearTimeout(redrawTimer);
  }
  redrawTimer = window.setTimeout(() => {
    drawRects();
  }, delay);
}

function normalizePageNo(raw: any): number {
  const n = Number(raw ?? 1);
  return Number.isFinite(n) && n > 0 ? n : 1;
}

function normalizeBbox(raw: any): [number, number, number, number] {
  if (Array.isArray(raw) && raw.length >= 4) {
    let x1 = Number(raw[0] ?? 0);
    let y1 = Number(raw[1] ?? 0);
    let x2 = Number(raw[2] ?? 0);
    let y2 = Number(raw[3] ?? 0);

    if (!Number.isFinite(x1)) x1 = 0;
    if (!Number.isFinite(y1)) y1 = 0;
    if (!Number.isFinite(x2)) x2 = 0;
    if (!Number.isFinite(y2)) y2 = 0;

    if (x1 > x2) [x1, x2] = [x2, x1];
    if (y1 > y2) [y1, y2] = [y2, y1];

    return [x1, y1, x2, y2];
  }

  if (raw && typeof raw === "object") {
    let startX = Number(raw.x0 ?? 0);
    let startY = Number(raw.y0 ?? 0);
    let endX = Number(raw.x1 ?? raw.x2 ?? 0);
    let endY = Number(raw.y1 ?? raw.y2 ?? 0);

    if (!Number.isFinite(startX)) startX = 0;
    if (!Number.isFinite(startY)) startY = 0;
    if (!Number.isFinite(endX)) endX = 0;
    if (!Number.isFinite(endY)) endY = 0;

    if (startX > endX) [startX, endX] = [endX, startX];
    if (startY > endY) [startY, endY] = [endY, startY];

    return [startX, startY, endX, endY];
  } // ← 여기 닫는 중괄호

  return [0, 0, 0, 0]; // ← fallback
} // ← 함수 닫는 중괄호

function getCanvasSize(canvas: HTMLCanvasElement) {
  const widthAttr = Number(canvas.width || 0);
  const heightAttr = Number(canvas.height || 0);

  if (widthAttr > 0 && heightAttr > 0) {
    return { width: widthAttr, height: heightAttr };
  }

  const rect = canvas.getBoundingClientRect();
  return {
    width: Math.max(1, rect.width),
    height: Math.max(1, rect.height),
  };
}

function getHighlightList(result: any): any[] {
  if (Array.isArray(result?.highlights)) return result.highlights;
  if (Array.isArray(result?.bbox_info)) return result.bbox_info;
  if (Array.isArray(result?.items)) return result.items;
  return [];
}

function drawRects() {
  const iframe = getIframe();
  const iframeDoc = getIframeDocument();

  if (!iframe || !iframeDoc) {
    flatRects.value = [];
    return;
  }

  const iframeRect = iframe.getBoundingClientRect();
  const nextRects: RectInfo[] = [];

  for (const result of props.searchResults || []) {
    const highlightList = getHighlightList(result);

    for (let i = 0; i < highlightList.length; i++) {
      const h = highlightList[i];
      const pageNo = normalizePageNo(
        h?.page_no ?? h?.page ?? result?.page_no ?? result?.page,
      );

      const pageEl = iframeDoc.querySelector(
        `.page[data-page-number="${pageNo}"]`,
      ) as HTMLElement | null;

      if (!pageEl) continue;

      const canvas =
        (pageEl.querySelector(
          ".canvasWrapper canvas",
        ) as HTMLCanvasElement | null) ||
        (pageEl.querySelector("canvas") as HTMLCanvasElement | null);

      if (!canvas) continue;

      const canvasRect = canvas.getBoundingClientRect();
      const sourceSize = getCanvasSize(canvas);

      const [x1, y1, x2, y2] = normalizeBbox(h?.bbox ?? h?.rect ?? h);

      const scaleX = canvasRect.width / Math.max(1, sourceSize.width);
      const scaleY = canvasRect.height / Math.max(1, sourceSize.height);

      const left = canvasRect.left - iframeRect.left + x1 * scaleX;
      const top = canvasRect.top - iframeRect.top + y1 * scaleY;
      const width = Math.max(2, (x2 - x1) * scaleX);
      const height = Math.max(2, (y2 - y1) * scaleY);

      if (!Number.isFinite(left) || !Number.isFinite(top)) continue;
      if (!Number.isFinite(width) || !Number.isFinite(height)) continue;

      nextRects.push({
        key: `${result?.id ?? "issue"}-${pageNo}-${i}-${x1}-${y1}-${x2}-${y2}`,
        issueId:
          typeof result?.id === "number"
            ? result.id
            : typeof result?._issue_id === "number"
              ? result._issue_id
              : null,
        page: pageNo,
        left,
        top,
        width,
        height,
        text: h?.text || result?.text || result?.chunk_text || "",
        section: result?.section || result?.display_path || "",
        rawResult: result,
        rawRect: h,
      });
    }
  }

  flatRects.value = nextRects;
}

function startObservers() {
  stopObservers();

  const run = () => scheduleRedraw(50);
  resizeHandler = run;
  window.addEventListener("resize", resizeHandler);

  observeTimer = window.setInterval(() => {
    drawRects();
  }, 500);
}

function stopObservers() {
  if (redrawTimer) {
    window.clearTimeout(redrawTimer);
    redrawTimer = null;
  }

  if (observeTimer) {
    window.clearInterval(observeTimer);
    observeTimer = null;
  }

  if (resizeHandler) {
    window.removeEventListener("resize", resizeHandler);
    resizeHandler = null;
  }
}

function handleClick(rect: RectInfo, idx: number) {
  emit("highlight-click", rect.rawResult, {
    ...rect.rawRect,
    issueId: rect.issueId,
    index: idx,
    page: rect.page,
  });
}

watch(
  () => props.searchResults,
  async () => {
    await nextTick();
    scheduleRedraw(50);
  },
  { deep: true },
);

watch(
  () => props.iframeId,
  async () => {
    await nextTick();
    scheduleRedraw(100);
  },
);

watch(
  () => props.pdfUrl,
  async () => {
    flatRects.value = [];
    await nextTick();
    scheduleRedraw(300);
    scheduleRedraw(800);
    scheduleRedraw(1500);
  },
);

onMounted(async () => {
  await nextTick();
  startObservers();
  scheduleRedraw(300);
  scheduleRedraw(800);
  scheduleRedraw(1500);
});

onBeforeUnmount(() => {
  stopObservers();
});
</script>

<style scoped>
.pdf-overlay-root {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 20;
}

.pdf-overlay-rect {
  position: absolute;
  box-sizing: border-box;
  border: 2px solid rgba(255, 140, 0, 0.95);
  background: rgba(255, 200, 0, 0.22);
  border-radius: 4px;
  pointer-events: auto;
  cursor: pointer;
  transition:
    transform 0.12s ease,
    box-shadow 0.12s ease,
    background-color 0.12s ease;
}

.pdf-overlay-rect:hover {
  background: rgba(255, 180, 0, 0.3);
  box-shadow: 0 0 0 2px rgba(255, 140, 0, 0.15);
}

.pdf-overlay-rect.active {
  border: 3px solid rgba(255, 87, 34, 1);
  background: rgba(255, 87, 34, 0.24);
  box-shadow: 0 0 0 3px rgba(255, 87, 34, 0.18);
}
</style>
