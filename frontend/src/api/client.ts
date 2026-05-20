export type Job = {
  id: string;
  analysis_type: string;
  status: "queued" | "running" | "succeeded" | "failed";
  parameters: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error: string | null;
  created_at: string;
  updated_at: string;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {})
    }
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export function runTcgaSurvival(payload: Record<string, unknown>) {
  return request<Job>("/api/tcga/survival", { method: "POST", body: JSON.stringify(payload) });
}

export function runTcgaCorrelation(payload: Record<string, unknown>) {
  return request<Job>("/api/tcga/correlation", { method: "POST", body: JSON.stringify(payload) });
}

export function runTumorNormal(payload: Record<string, unknown>) {
  return request<Job>("/api/tcga/tumor-normal", { method: "POST", body: JSON.stringify(payload) });
}

export function runTcgaExpression(payload: Record<string, unknown>) {
  return request<Job>("/api/tcga/expression", { method: "POST", body: JSON.stringify(payload) });
}

export function runOra(payload: Record<string, unknown>) {
  return request<Job>("/api/ora/ora", { method: "POST", body: JSON.stringify(payload) });
}

export function runGsea(payload: Record<string, unknown>) {
  return request<Job>("/api/ora/gsea", { method: "POST", body: JSON.stringify(payload) });
}

export function listJobs() {
  return request<Job[]>("/api/jobs");
}
