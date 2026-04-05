import { useState, useCallback } from "react";
import { Uploader } from "./components/Uploader";
import { ResultView } from "./components/ResultView";
import type { ProcessingResult, ProcessingStatus } from "./api/client";

type AppPhase = "idle" | "uploading" | "processing" | "done" | "error";

export default function App() {
  const [phase, setPhase] = useState<AppPhase>("idle");
  const [status, setStatus] = useState<ProcessingStatus | null>(null);
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [error, setError] = useState<string>("");

  const handleUploadStart = useCallback(() => {
    setPhase("uploading");
    setError("");
  }, []);

  const handleUploadSuccess = useCallback((jobId: string) => {
    setPhase("processing");

    const pollStatus = async () => {
      try {
        const data: ProcessingStatus = await fetch(
          `/api/status/${jobId}`
        ).then((r) => r.json());
        setStatus(data);

        if (data.status === "completed") {
          const resultData: ProcessingResult = await fetch(
            `/api/result/${jobId}`
          ).then((r) => r.json());
          setResult(resultData);
          setPhase("done");
        } else if (data.status === "failed") {
          setError(data.error || "Processing failed");
          setPhase("error");
        } else {
          setTimeout(pollStatus, 1000);
        }
      } catch {
        setError("Failed to check status");
        setPhase("error");
      }
    };

    setTimeout(pollStatus, 1000);
  }, []);

  const handleUploadError = useCallback((message: string) => {
    setError(message);
    setPhase("error");
  }, []);

  const handleReset = useCallback(() => {
    setPhase("idle");
    setStatus(null);
    setResult(null);
    setError("");
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Document Processor</h1>
        <p className="app-subtitle">
          Загрузите документ для извлечения текста и таблиц
        </p>
      </header>

      <main className="app-main">
        {phase === "idle" && (
          <Uploader
            onUploadStart={handleUploadStart}
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
          />
        )}

        {phase === "uploading" && (
          <div className="status-card">
            <div className="spinner" />
            <p>Загрузка файла...</p>
          </div>
        )}

        {phase === "processing" && status && (
          <div className="status-card">
            <div className="spinner" />
            <p>Обработка документа...</p>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${status.progress}%` }}
              />
            </div>
            <span className="progress-text">{status.progress}%</span>
          </div>
        )}

        {phase === "done" && result && (
          <ResultView result={result} onReset={handleReset} />
        )}

        {phase === "error" && (
          <div className="error-card">
            <p className="error-message">{error}</p>
            <button className="btn btn-primary" onClick={handleReset}>
              Попробовать снова
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
