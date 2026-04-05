export interface UploadResponse {
  file_id: string;
  filename: string;
  size: number;
  message: string;
}

export interface ProcessRequest {
  file_id: string;
  formats: string[];
  quality_preset?: string;
}

export interface ProcessResponse {
  task_id: string;
  message: string;
}

export interface TaskStatus {
  task_id: string;
  status: string;
  progress?: number;
  step?: string;
  error?: string;
}

export interface ProcessingTask {
  taskId: string;
  fileId: string;
  filename: string;
  status: string;
  progress: number;
  step: string;
  formats: string[];
}
