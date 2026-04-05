export interface UploadResponse {
  job_id: string;
  filename: string;
  status: string;
}

export interface ProcessingStatus {
  job_id: string;
  status: "processing" | "completed" | "failed";
  progress: number;
  error?: string;
  document_type?: string;
}

export interface ProcessingResult {
  job_id: string;
  document_type: string;
  text_regions: Array<{ text: string; confidence: number }>;
  table_regions: Array<{ cells: string[][] }>;
  full_text: string;
  processing_time_ms: number;
}

const API_BASE = import.meta.env.VITE_API_URL || "";

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Upload failed");
  }

  return response.json();
}

export async function getJobStatus(jobId: string): Promise<ProcessingStatus> {
  const response = await fetch(`${API_BASE}/api/status/${jobId}`);
  return response.json();
}

export async function getJobResult(jobId: string): Promise<ProcessingResult> {
  const response = await fetch(`${API_BASE}/api/result/${jobId}`);
  return response.json();
}

export function getDownloadUrl(jobId: string, format: string): string {
  return `${API_BASE}/api/download/${jobId}/${format}`;
}
