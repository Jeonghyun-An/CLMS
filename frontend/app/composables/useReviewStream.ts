/**
 * useReviewStream.ts
 * 검토 SSE 스트림 수신 + 상태 관리
 *
 * 사용법:
 *   const { startReview, isReviewing, docResults, totalErrors } = useReviewStream()
 *   await startReview(documents.value)
 */

import { ref, computed } from 'vue'

// ─── 타입 ─────────────────────────────────────────────────────────────────

export interface LegalCitation {
  article_id: string
  source: string
  article: string
  title: string
  relevant_excerpt: string
}

export interface ReviewIssue {
  issue_id: string
  rule_id: string
  issue_type: string
  severity: 'error' | 'warning' | 'info'
  title: string
  description: string
  location?: string
  detected_value?: string
  expected_value?: string
  citations: LegalCitation[]
  rag_confidence: number
  retrieval_source: string
}

export interface DocumentReviewResult {
  doc_id: string
  doc_name: string
  category: string
  status: string
  issues: ReviewIssue[]
  summary: string
  error_count: number
  warning_count: number
  info_count: number
}

export interface SSEEvent {
  event: 'started' | 'step' | 'issue_found' | 'doc_done' | 'job_done' | 'error'
  job_id: string
  doc_id?: string
  doc_name?: string
  message: string
  step?: string
  progress: number
  issue?: ReviewIssue
  result?: DocumentReviewResult
}

export interface ReviewDocument {
  id: string
  name: string
  category: string
  size: number
}

// ─── composable ───────────────────────────────────────────────────────────

export function useReviewStream() {
  const isReviewing   = ref(false)
  const currentStep   = ref('')
  const progress      = ref(0)
  const jobId         = ref<string | null>(null)
  const error         = ref<string | null>(null)
  const events        = ref<SSEEvent[]>([])
  const docResults    = ref<Map<string, DocumentReviewResult>>(new Map())

  const totalErrors   = computed(() =>
    [...docResults.value.values()].reduce((s, r) => s + r.error_count, 0)
  )
  const totalWarnings = computed(() =>
    [...docResults.value.values()].reduce((s, r) => s + r.warning_count, 0)
  )
  const allIssues = computed(() =>
    [...docResults.value.values()].flatMap(r => r.issues)
  )

  function _handle(evt: SSEEvent) {
    events.value.push(evt)
    switch (evt.event) {
      case 'started':
        jobId.value = evt.job_id; progress.value = 0; break
      case 'step':
        currentStep.value = evt.step ?? evt.message
        progress.value = evt.progress; break
      case 'doc_done':
        if (evt.result) docResults.value.set(evt.doc_id!, evt.result)
        progress.value = evt.progress; break
      case 'job_done':
        progress.value = 1; isReviewing.value = false; break
      case 'error':
        error.value = evt.message; isReviewing.value = false; break
    }
  }

  async function startReview(documents: ReviewDocument[]) {
    if (isReviewing.value || !documents.length) return

    isReviewing.value = true
    events.value = []
    docResults.value = new Map()
    progress.value = 0
    error.value = null

    try {
      const res = await fetch('/api/v1/review/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documents }),
      })
      if (!res.ok) throw new Error(`서버 오류: ${res.status}`)

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buf = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const lines = buf.split('\n')
        buf = lines.pop() ?? ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try { _handle(JSON.parse(line.slice(6))) } catch {}
        }
      }
    } catch (e: any) {
      error.value = e.message ?? '알 수 없는 오류'
      isReviewing.value = false
    }
  }

  function reset() {
    isReviewing.value = false
    events.value = []
    docResults.value = new Map()
    progress.value = 0
    error.value = null
    jobId.value = null
  }

  return {
    isReviewing, currentStep, progress, jobId, error, events,
    docResults, totalErrors, totalWarnings, allIssues,
    startReview, reset,
  }
}
