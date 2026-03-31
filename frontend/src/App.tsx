import { useState } from 'react';
import { FileUpload } from './components/FileUpload/FileUpload';
import { ProcessingQueue } from './components/ProcessingQueue/ProcessingQueue';
import { Results } from './components/Results/Results';
import { startProcessing } from './services/api';
import type { ProcessingTask } from './types';
import './App.css';

function App() {
  const [processingTasks, setProcessingTasks] = useState<ProcessingTask[]>([]);
  const [completedTasks, setCompletedTasks] = useState<ProcessingTask[]>([]);
  const [selectedFormats, setSelectedFormats] = useState<string[]>(['txt', 'docx', 'xlsx', 'csv']);
  const [qualityPreset, setQualityPreset] = useState<string>("balanced");

  const handleUploadComplete = async (uploads: Array<{ fileId: string; filename: string }>) => {
    for (const upload of uploads) {
      try {
        const response = await startProcessing(upload.fileId, selectedFormats, qualityPreset);

        const newTask: ProcessingTask = {
          taskId: response.task_id,
          fileId: upload.fileId,
          filename: upload.filename,
          status: 'PENDING',
          progress: 0,
          step: '',
          formats: selectedFormats,
        };

        setProcessingTasks(prev => [...prev, newTask]);
      } catch (error) {
        console.error('Error starting processing:', error);
        alert(`Ошибка запуска обработки для ${upload.filename}`);
      }
    }
  };

  const handleTaskComplete = (taskId: string) => {
    setProcessingTasks(prev => {
      const task = prev.find(t => t.taskId === taskId);
      if (task) {
        setCompletedTasks(completed => [...completed, { ...task, status: 'SUCCESS' }]);
      }
      return prev.filter(t => t.taskId !== taskId);
    });
  };

  const toggleFormat = (format: string) => {
    setSelectedFormats(prev =>
      prev.includes(format)
        ? prev.filter(f => f !== format)
        : [...prev, format]
    );
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>OCR Web Service</h1>
        <p>Распознавание текста и таблиц из сканированных документов</p>
      </header>

      <main className="app-main">
        <div className="format-selector">
          <h3>Форматы экспорта:</h3>
          <div className="format-options">
            {['txt', 'docx', 'xlsx', 'csv'].map(format => (
              <label key={format} className="format-checkbox">
                <input
                  type="checkbox"
                  checked={selectedFormats.includes(format)}
                  onChange={() => toggleFormat(format)}
                />
                <span>{format.toUpperCase()}</span>
              </label>
            ))}
          </div>

          <div className="quality-selector">
            <h3>Качество распознавания:</h3>
            <div className="quality-options">
              <label className="quality-option">
                <input
                  type="radio"
                  name="quality"
                  value="fast"
                  checked={qualityPreset === "fast"}
                  onChange={(e) => setQualityPreset(e.target.value)}
                />
                <span>⚡ Быстрый (менее точно, но быстрее)</span>
              </label>
              <label className="quality-option">
                <input
                  type="radio"
                  name="quality"
                  value="balanced"
                  checked={qualityPreset === "balanced"}
                  onChange={(e) => setQualityPreset(e.target.value)}
                />
                <span>✓ Сбалансированный (по умолчанию)</span>
              </label>
              <label className="quality-option">
                <input
                  type="radio"
                  name="quality"
                  value="high_quality"
                  checked={qualityPreset === "high_quality"}
                  onChange={(e) => setQualityPreset(e.target.value)}
                />
                <span>🎯 Высокое (максимальная точность)</span>
              </label>
            </div>
          </div>
        </div>

        <FileUpload onUploadComplete={handleUploadComplete} />

        <ProcessingQueue
          tasks={processingTasks}
          onTaskComplete={handleTaskComplete}
        />

        <Results completedTasks={completedTasks} />
      </main>

      <footer className="app-footer">
        <p>Поддерживаемые форматы: PDF, JPG, PNG, TIFF | Максимальный размер: 5MB</p>
      </footer>
    </div>
  );
}

export default App;
