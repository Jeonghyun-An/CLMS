// composables/useApi.ts
// 백엔드 API 클라이언트

const BASE = "/api/v1";

export function useApi() {
  const projectId = useState<number>("projectId", () => 1);

  // ── 프로젝트
  async function getProject(id: number) {
    return $fetch(`${BASE}/projects/${id}`);
  }
  async function createProject(name: string, description?: string) {
    return $fetch(`${BASE}/projects`, {
      method: "POST",
      body: { name, description },
    });
  }

  // ── 문서 목록
  async function getDocuments(reviewRunId?: number) {
    const q = reviewRunId ? `?review_run_id=${reviewRunId}` : "";
    return $fetch(`${BASE}/projects/${projectId.value}/documents${q}`);
  }

  // ── 검토 이슈
  async function getIssues(reviewRunId: number, documentId?: number) {
    const q = documentId ? `?document_id=${documentId}&size=100` : "?size=100";
    return $fetch(`${BASE}/reviews/${reviewRunId}/issues${q}`);
  }

  async function getIssueSummary(reviewRunId: number) {
    return $fetch(`${BASE}/reviews/${reviewRunId}/summary`);
  }

  // ── 하이라이트
  async function getHighlights(reviewRunId: number, documentId: number) {
    return $fetch(
      `${BASE}/projects/${projectId.value}/reviews/${reviewRunId}/highlights/${documentId}`,
    );
  }

  // ── 체크리스트
  async function getChecklist(reviewRunId: number) {
    return $fetch(
      `${BASE}/projects/${projectId.value}/reviews/${reviewRunId}/checklist`,
    );
  }
  async function getChecklistForm() {
    return $fetch(`${BASE}/projects/${projectId.value}/checklist/form`);
  }
  async function saveChecklistForm(
    reviewRunId: number,
    selections: Record<string, any>,
  ) {
    return $fetch(`${BASE}/projects/${projectId.value}/checklist/save`, {
      method: "POST",
      body: { review_run_id: reviewRunId, selections },
    });
  }

  // ── 승인선
  async function getApprovalLine(reviewRunId: number) {
    return $fetch(`${BASE}/reviews/${reviewRunId}/approval-line`);
  }

  // ── 리포트 다운로드 URL
  function getReportDownloadUrl(reviewRunId: number) {
    return `${BASE}/projects/${projectId.value}/reviews/${reviewRunId}/report/download`;
  }

  // ── 채팅 스트림
  function chatStream(
    question: string,
    reviewRunId: number,
    documentId: number,
    onChunk: (text: string) => void,
    onDone: () => void,
    onError: (msg: string) => void,
  ) {
    fetch(`${BASE}/projects/${projectId.value}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        review_run_id: reviewRunId,
        document_id: documentId,
      }),
    })
      .then(async (res) => {
        const reader = res.body!.getReader();
        const decoder = new TextDecoder();
        let buf = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const lines = buf.split("\n");
          buf = lines.pop() || "";
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const evt = JSON.parse(line.slice(6));
              if (evt.type === "chunk") onChunk(evt.content);
              if (evt.type === "done") onDone();
              if (evt.type === "error") onError(evt.content);
            } catch {}
          }
        }
      })
      .catch((e) => onError(String(e)));
  }

  // ── 파일 업로드 스트림
  function uploadStream(
    files: File[],
    useLlm: boolean,
    onEvent: (evt: Record<string, any>) => void,
  ): Promise<number> {
    return new Promise((resolve, reject) => {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      form.append("use_llm", String(useLlm));

      fetch(`${BASE}/projects/${projectId.value}/reviews/upload/stream`, {
        method: "POST",
        body: form,
      })
        .then(async (res) => {
          const reader = res.body!.getReader();
          const decoder = new TextDecoder();
          let buf = "";
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buf += decoder.decode(value, { stream: true });
            const lines = buf.split("\n");
            buf = lines.pop() || "";
            for (const line of lines) {
              if (!line.startsWith("data: ")) continue;
              try {
                const evt = JSON.parse(line.slice(6));
                onEvent(evt);
                if (evt.type === "all_done") resolve(evt.review_run_id);
                if (evt.type === "error") reject(new Error(evt.message));
              } catch {}
            }
          }
        })
        .catch(reject);
    });
  }

  return {
    projectId,
    getProject,
    createProject,
    getDocuments,
    getIssues,
    getIssueSummary,
    getHighlights,
    getChecklist,
    getChecklistForm,
    saveChecklistForm,
    getApprovalLine,
    getReportDownloadUrl,
    chatStream,
    uploadStream,
  };
}
