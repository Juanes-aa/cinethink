export interface SessionSummary {
  id: string
  movie_id: string
  movie_title: string
  movie_poster_url: string | null
  status: 'active' | 'closed'
  started_at: string
  closed_at: string | null
  has_tags: boolean
}

export interface AnalysisMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface SemanticTag {
  id: string
  session_id: string
  tag_type: string
  tag_value: string
  confidence: number | null
}
