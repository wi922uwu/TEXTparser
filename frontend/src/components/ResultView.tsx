import { getDownloadUrl } from "../api/client";
import type { ProcessingResult } from "../api/client";

interface ResultViewProps {
  result: ProcessingResult;
  onReset: () => void;
}

export function ResultView({ result, onReset }: ResultViewProps) {
  const formats = getAvailableFormats(result);

  return (
    <div className="result-card">
      <div className="result-header">
        <h2>Обработка завершена</h2>
        <span className="result-time">
          {result.processing_time_ms} мс
        </span>
      </div>

      <div className="result-type">
        Тип документа:{" "}
        <strong>
          {result.document_type === "text" && "Текст"}
          {result.document_type === "table" && "Таблица"}
          {result.document_type === "combined" && "Комбинированный"}
        </strong>
      </div>

      {result.text_regions.length > 0 && (
        <details className="result-preview">
          <summary>Предпросмотр текста</summary>
          <pre className="result-text">{result.full_text}</pre>
        </details>
      )}

      {result.table_regions.length > 0 && (
        <div className="result-tables">
          <h3>Обнаружено таблиц: {result.table_regions.length}</h3>
          {result.table_regions.map((table: { cells: string[][] }, i: number) => (
            <details key={i} className="table-preview">
              <summary>Таблица {i + 1}</summary>
              <table className="data-table">
                <tbody>
                  {table.cells.map((row: string[], ri: number) => (
                    <tr key={ri}>
                      {row.map((cell: string, ci: number) => (
                        <td key={ci}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
          ))}
        </div>
      )}

      <div className="download-section">
        <h3>Скачать результат</h3>
        <div className="download-buttons">
          {formats.map((fmt) => (
            <a
              key={fmt}
              href={getDownloadUrl(result.job_id, fmt)}
              className="btn btn-download"
              download
            >
              {fmt.toUpperCase()}
            </a>
          ))}
        </div>
      </div>

      <button className="btn btn-secondary" onClick={onReset}>
        Загрузить другой документ
      </button>
    </div>
  );
}

function getAvailableFormats(result: ProcessingResult): string[] {
  if (result.document_type === "table") {
    return ["xlsx"];
  }
  const formats = ["txt", "docx"];
  if (result.table_regions.length > 0) {
    formats.push("xlsx");
  }
  return formats;
}
