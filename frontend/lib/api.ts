const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface Creator {
  handle: string;
  total_views: number;
  engagement_rate: number;
  video_count: number;
  verified: boolean;
  sample_caption: string | null;
}

export interface SummaryMeta {
  total_creators: number;
  promising_count: number;
  date_range: [string, string];
}

export interface SummaryResponse {
  meta: SummaryMeta;
  creators: Creator[];
}

export async function fetchSummary(): Promise<SummaryResponse> {
  const res = await fetch(`${API_BASE_URL}/api/summary`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to load summary (${res.status})`);
  }
  return res.json();
}

export interface ChatSource {
  tool: string;
  input: Record<string, unknown>;
  output: unknown;
}

export interface ChatResponse {
  answer: string;
  kind: "computed" | "grounded_opinion" | "opinion";
  sources: ChatSource[];
}

export async function askQuestion(question: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Chat request failed (${res.status})`);
  }

  return res.json();
}
