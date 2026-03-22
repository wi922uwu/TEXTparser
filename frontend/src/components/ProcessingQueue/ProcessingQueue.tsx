import { useEffect, useState } from 'react';
import { getTaskStatus } from '../../services/api';
import type { ProcessingTask } from '../../types';
import './ProcessingQueue.css';

interface ProcessingQueueProps {
  tasks: ProcessingTask[];
  onTaskComplete: (taskId: string) => void;
}

export const ProcessingQueue: React.FC<ProcessingQueueProps> = ({ tasks, onTaskComplete }) => {
  const [taskStatuses, setTaskStatuses] = useState<Map<string, ProcessingTask>>(new Map());

  useEffect(() => {
    const interval = setInterval(async () => {
      for (const task of tasks) {
        if (task.status === 'SUCCESS' || task.status === 'FAILURE') {
          continue;
        }

        try {
          const status = await getTaskStatus(task.taskId);

          setTaskStatuses(prev => {
            const updated = new Map(prev);
            updated.set(task.taskId, {
              ...task,
              status: status.status,
              progress: status.progress || 0,
              step: status.step || '',
            });
            return updated;
          });

          if (status.status === 'SUCCESS') {
            onTaskComplete(task.taskId);
          }
        } catch (error) {
          console.error(`Error checking status for ${task.taskId}:`, error);
        }
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [tasks, onTaskComplete]);

  const getDisplayStatus = (task: ProcessingTask): ProcessingTask => {
    return taskStatuses.get(task.taskId) || task;
  };

  const getStepText = (step: string): string => {
    const steps: Record<string, string> = {
      'loading': 'Загрузка файла',
      'pdf_conversion': 'Конвертация PDF',
      'preprocessing': 'Предобработка',
      'ocr_processing': 'Распознавание текста',
      'exporting': 'Экспорт результатов',
      'completed': 'Завершено',
    };
    return steps[step] || step;
  };

  if (tasks.length === 0) {
    return null;
  }

  return (
    <div className="processing-queue">
      <h2>Обработка</h2>
      <div className="queue-list">
        {tasks.map(task => {
          const currentTask = getDisplayStatus(task);
          return (
            <div key={task.taskId} className="queue-item">
              <div className="task-header">
                <span className="filename">{task.filename}</span>
                <span className="status">{currentTask.status}</span>
              </div>

              {currentTask.status === 'PROGRESS' && (
                <>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${currentTask.progress}%` }}
                    />
                  </div>
                  <div className="task-info">
                    <span>{getStepText(currentTask.step)}</span>
                    <span>{currentTask.progress}%</span>
                  </div>
                </>
              )}

              {currentTask.status === 'SUCCESS' && (
                <div className="task-success">✓ Обработка завершена</div>
              )}

              {currentTask.status === 'FAILURE' && (
                <div className="task-error">✗ Ошибка обработки</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
