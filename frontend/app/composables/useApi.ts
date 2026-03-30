const BASE = "/api/v1";

type ApiParams = Record<string, string | number | boolean | undefined | null>;

function buildUrl(path: string, params?: ApiParams) {
  const qs = new URLSearchParams();

  Object.entries(params || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    qs.set(key, String(value));
  });

  return qs.toString() ? `${BASE}${path}?${qs.toString()}` : `${BASE}${path}`;
}

export function useApi() {
  const projectId = useState<number>("projectId", () => 1);

  const withProject = (params?: ApiParams): ApiParams => ({
    project_id: projectId.value,
    ...(params || {}),
  });

  async function getProjects() {
    return $fetch(buildUrl("/projects"));
  }

  async function getProject(id: number) {
    return $fetch(buildUrl(`/projects/${id}`));
  }

  async function createProject(name: string, description?: string) {
    return $fetch(buildUrl("/projects"), {
      method: "POST",
      body: { name, description },
    });
  }

  async function getDocuments(reviewRunId: number) {
    return $fetch(
      buildUrl(`/reviews/reviews/${reviewRunId}/documents`, withProject()),
    );
  }

  async function getIssues(reviewRunId: number) {
    return $fetch(
      buildUrl(
        `/reviews/reviews/${reviewRunId}/issues`,
        withProject({ size: 100 }),
      ),
    );
  }

  async function getIssueSummary(reviewRunId: number) {
    return $fetch(
      buildUrl(`/reviews/reviews/${reviewRunId}/summary`, withProject()),
    );
  }

  async function getApprovalLine(reviewRunId: number) {
    return $fetch(
      buildUrl(`/reviews/reviews/${reviewRunId}/approval-line`, withProject()),
    );
  }

  async function getHighlights(reviewRunId: number, documentId: number) {
    return $fetch(
      buildUrl(
        `/reports/reviews/${reviewRunId}/highlights/${documentId}`,
        withProject(),
      ),
    );
  }

  async function getChecklist(reviewRunId: number) {
    return $fetch(
      buildUrl(`/reports/reviews/${reviewRunId}/checklist`, withProject()),
    );
  }

  async function getChecklistForm() {
    return $fetch(buildUrl("/checklist_form/form", withProject()));
  }

  async function saveChecklistForm(
    reviewRunId: number,
    selections: Record<string, any>,
  ) {
    return $fetch(buildUrl("/checklist_form/save", withProject()), {
      method: "POST",
      body: { review_run_id: reviewRunId, selections },
    });
  }

  function getReportDownloadUrl(reviewRunId: number) {
    return buildUrl(
      `/reports/reviews/${reviewRunId}/report/download`,
      withProject(),
    );
  }

  function getPdfViewerUrl(reviewRunId: number, documentId: number) {
    const pdfApi = encodeURIComponent(
      buildUrl(
        `/reviews/reviews/${reviewRunId}/pdf/${documentId}`,
        withProject(),
      ),
    );
    return `/pdfjs/web/viewer.html?file=${pdfApi}`;
  }

  function chatStream(
    question: string,
    reviewRunId: number,
    documentId: number,
    onChunk: (text: string) => void,
    onDone: () => void,
    onError: (msg: string) => void,
  ) {
    fetch(buildUrl("/chat/stream", withProject()), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        review_run_id: reviewRunId,
        document_id: documentId,
      }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text().catch(() => "");
          onError(text || `HTTP ${res.status}`);
          return;
        }

        if (!res.body) {
          onError("응답 body가 없습니다.");
          return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buf += decoder.decode(value, { stream: true });
          const events = buf.split("\n\n");
          buf = events.pop() || "";

          for (const event of events) {
            const line = event.split("\n").find((v) => v.startsWith("data: "));
            if (!line) continue;

            try {
              const evt = JSON.parse(line.slice(6));
              if (evt.type === "chunk") onChunk(evt.content ?? "");
              else if (evt.type === "done") onDone();
              else if (evt.type === "error")
                onError(evt.content || evt.message || "오류");
            } catch (e) {
              console.error("chat SSE parse error:", e, event);
            }
          }
        }
      })
      .catch((e) => onError(String(e)));
  }

  function uploadStream(
    files: File[],
    useLlm: boolean,
    onEvent: (evt: Record<string, any>) => void,
    fileCategories?: Record<string, string>,
  ): Promise<number> {
    return new Promise((resolve, reject) => {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      form.append("use_llm", String(useLlm));

      if (fileCategories && Object.keys(fileCategories).length > 0) {
        form.append("file_categories", JSON.stringify(fileCategories));
      }

      fetch(buildUrl("/upload_review/upload/stream", withProject()), {
        method: "POST",
        body: form,
      })
        .then(async (res) => {
          if (!res.ok) {
            const text = await res.text().catch(() => "");
            reject(new Error(text || `HTTP ${res.status}`));
            return;
          }

          if (!res.body) {
            reject(new Error("응답 body가 없습니다."));
            return;
          }

          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buf = "";

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buf += decoder.decode(value, { stream: true });
            const events = buf.split("\n\n");
            buf = events.pop() || "";

            for (const event of events) {
              const line = event
                .split("\n")
                .find((v) => v.startsWith("data: "));
              if (!line) continue;

              try {
                const evt = JSON.parse(line.slice(6));
                onEvent(evt);

                if (evt.type === "all_done" && evt.review_run_id) {
                  resolve(Number(evt.review_run_id));
                } else if (evt.type === "error") {
                  reject(new Error(evt.message || "업로드 오류"));
                }
              } catch (e) {
                console.error("upload SSE parse error:", e, event);
              }
            }
          }
        })
        .catch(reject);
    });
  }

  return {
    projectId,
    getProjects,
    getProject,
    createProject,
    getDocuments,
    getIssues,
    getIssueSummary,
    getApprovalLine,
    getHighlights,
    getChecklist,
    getChecklistForm,
    saveChecklistForm,
    getReportDownloadUrl,
    getPdfViewerUrl,
    chatStream,
    uploadStream,
  };
}
