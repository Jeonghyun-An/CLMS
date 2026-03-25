/**
 * useDocumentStore.ts
 * 문서 업로드·카테고리 상태 관리
 *
 * PoC: localStorage 저장 (새로고침 후 복원)
 * 실제 연동 시: localStorage → PATCH /api/v1/upload/documents/:id 교체
 */

import { ref, computed } from "vue";

export type DocumentCategory =
  | "contract"
  | "specification"
  | "cost"
  | "guideline"
  | "law"
  | "approval"
  | "other";

export interface UploadedDocument {
  id: string;
  name: string;
  size: number;
  category: DocumentCategory;
  autoCategory: DocumentCategory;
  uploadedAt: string;
  status: "pending" | "processing" | "done" | "error";
  fileKey?: string;
}

export interface CategoryConfig {
  id: DocumentCategory;
  label: string;
  description: string;
  color: string;
  keywords: string[];
}

export const CATEGORY_CONFIGS: CategoryConfig[] = [
  {
    id: "contract",
    label: "계약서",
    description: "공사계약서, 용역계약서, 물품계약서 등",
    color: "#4F46E5",
    keywords: [
      "계약서",
      "계약",
      "공사계약",
      "용역계약",
      "물품계약",
      "contract",
      "협약서",
      "약정서",
    ],
  },
  {
    id: "specification",
    label: "시방서 / 설계내역서",
    description: "시방서, 설계내역서, 도면 등",
    color: "#0891B2",
    keywords: [
      "시방서",
      "시방",
      "설계내역서",
      "설계내역",
      "도면",
      "설계도",
      "설계서",
      "내역서",
    ],
  },
  {
    id: "cost",
    label: "산출내역서 / 예산서",
    description: "원가계산서, 산출내역서, 예산서 등",
    color: "#059669",
    keywords: [
      "산출내역서",
      "산출내역",
      "예산서",
      "예산",
      "원가계산서",
      "원가",
      "노임단가",
      "견적서",
    ],
  },
  {
    id: "guideline",
    label: "가이드라인 / 내부지침",
    description: "내부 운영지침, 매뉴얼 등",
    color: "#D97706",
    keywords: [
      "가이드라인",
      "지침",
      "내부지침",
      "매뉴얼",
      "안내",
      "규정집",
      "지침서",
    ],
  },
  {
    id: "law",
    label: "법령",
    description: "법률, 시행령, 시행규칙, 조례 등",
    color: "#DC2626",
    keywords: [
      "법",
      "법령",
      "법률",
      "시행령",
      "시행규칙",
      "조례",
      "규칙",
      "지방계약법",
    ],
  },
  {
    id: "approval",
    label: "결재 / 전결규정",
    description: "사무전결규정, 결재선, 전결 기준 등",
    color: "#7C3AED",
    keywords: [
      "전결",
      "전결규정",
      "사무전결",
      "결재",
      "결재선",
      "결재규정",
      "위임전결",
    ],
  },
  {
    id: "other",
    label: "기타 / 미분류",
    description: "분류되지 않은 문서",
    color: "#6B7280",
    keywords: [],
  },
];

const STORAGE_KEY = "clms_docs_v1";

function classifyByName(name: string): DocumentCategory {
  const n = name
    .replace(/\.[^.]+$/, "")
    .replace(/[-_\s]/g, "")
    .toLowerCase();
  let best: DocumentCategory = "other",
    score = 0;
  for (const cfg of CATEGORY_CONFIGS) {
    if (cfg.id === "other") continue;
    const s = cfg.keywords.reduce(
      (acc, k) =>
        acc + (n.includes(k.toLowerCase().replace(/\s/g, "")) ? k.length : 0),
      0,
    );
    if (s > score) {
      best = cfg.id;
      score = s;
    }
  }
  return best;
}

function genId() {
  return `doc_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

export function useDocumentStore() {
  const documents = ref<UploadedDocument[]>([]);

  function _persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(documents.value));
    } catch {}
  }

  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) documents.value = JSON.parse(raw);
    } catch {}
  }

  function addFiles(files: File[], forceCategory?: DocumentCategory) {
    const newDocs = files.map((f): UploadedDocument => {
      const auto = classifyByName(f.name);
      return {
        id: genId(),
        name: f.name,
        size: f.size,
        category: forceCategory ?? auto,
        autoCategory: auto,
        uploadedAt: new Date().toISOString(),
        status: "pending",
      };
    });
    documents.value.push(...newDocs);
    _persist();

    /**
     * TODO: 백엔드 연동 시 여기서 파일 업로드
     * const form = new FormData()
     * files.forEach(f => form.append('files', f))
     * await $fetch('/api/v1/upload/documents', { method: 'POST', body: form })
     */
    return newDocs;
  }

  function moveDocument(id: string, category: DocumentCategory) {
    const doc = documents.value.find((d) => d.id === id);
    if (!doc) return;
    doc.category = category;
    _persist();

    /**
     * TODO: 백엔드 연동 시 카테고리 변경 저장
     * await $fetch(`/api/v1/upload/documents/${id}`, {
     *   method: 'PATCH', body: { category }
     * })
     */
  }

  function removeDocument(id: string) {
    documents.value = documents.value.filter((d) => d.id !== id);
    _persist();
  }

  function updateStatus(id: string, status: UploadedDocument["status"]) {
    const doc = documents.value.find((d) => d.id === id);
    if (doc) {
      doc.status = status;
      _persist();
    }
  }

  function clearAll() {
    documents.value = [];
    localStorage.removeItem(STORAGE_KEY);
  }

  const byCategory = computed(() => {
    const map: Record<DocumentCategory, UploadedDocument[]> = {} as any;
    for (const cfg of CATEGORY_CONFIGS) map[cfg.id] = [];
    for (const doc of documents.value) map[doc.category]?.push(doc);
    return map;
  });

  const pendingCount = computed(
    () => documents.value.filter((d) => d.status === "pending").length,
  );

  return {
    documents,
    byCategory,
    pendingCount,
    load,
    addFiles,
    moveDocument,
    removeDocument,
    updateStatus,
    clearAll,
    CATEGORY_CONFIGS,
    classifyByName,
  };
}
