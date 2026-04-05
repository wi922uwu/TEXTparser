import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

const ACCEPTED_FILES = {
  "application/pdf": [".pdf"],
  "image/jpeg": [".jpg", ".jpeg"],
  "image/png": [".png"],
  "image/tiff": [".tiff", ".tif"],
};

interface UploaderProps {
  onUploadStart: () => void;
  onUploadSuccess: (jobId: string) => void;
  onUploadError: (message: string) => void;
}

export function Uploader({
  onUploadStart,
  onUploadSuccess,
  onUploadError,
}: UploaderProps) {
  const handleFile = useCallback(
    async (file: File) => {
      onUploadStart();

      try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("/api/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const error = await response.json();
          onUploadError(error.detail || "Upload failed");
          return;
        }

        const data = await response.json();
        onUploadSuccess(data.job_id);
      } catch {
        onUploadError("Network error. Check backend connection.");
      }
    },
    [onUploadStart, onUploadSuccess, onUploadError]
  );

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        handleFile(acceptedFiles[0]!);
      }
    },
    [handleFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILES,
    maxFiles: 1,
  });

  return (
    <div
      {...getRootProps()}
      className={`dropzone ${isDragActive ? "dropzone-active" : ""}`}
    >
      <input {...getInputProps()} />
      <div className="dropzone-content">
        <svg
          className="dropzone-icon"
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <p className="dropzone-title">
          Перетащите файл сюда или{" "}
          <span className="dropzone-link">выберите файл</span>
        </p>
        <p className="dropzone-formats">
          PDF, JPG, PNG, TIFF (многостраничные)
        </p>
      </div>
    </div>
  );
}
