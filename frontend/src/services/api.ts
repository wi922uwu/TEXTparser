import axios from 'axios';
import type { UploadResponse, ProcessRequest, ProcessResponse, TaskStatus } from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 300000, // 5 minutes
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadFile = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<UploadResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

export const uploadFiles = async (files: File[]): Promise<UploadResponse[]> => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));

  const response = await api.post<UploadResponse[]>('/upload/batch', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

export const startProcessing = async (
  fileId: string,
  formats: string[]
): Promise<ProcessResponse> => {
  const request: ProcessRequest = {
    file_id: fileId,
    formats,
  };

  const response = await api.post<ProcessResponse>('/process', request);
  return response.data;
};

export const getTaskStatus = async (taskId: string): Promise<TaskStatus> => {
  const response = await api.get<TaskStatus>(`/status/${taskId}`);
  return response.data;
};

export const downloadResult = async (taskId: string, format: string): Promise<Blob> => {
  const response = await api.get(`/result/${taskId}`, {
    params: { format },
    responseType: 'blob',
  });

  return response.data;
};

export const downloadArchive = async (taskId: string): Promise<Blob> => {
  const response = await api.get(`/result/${taskId}/archive`, {
    responseType: 'blob',
  });

  return response.data;
};

export default api;
