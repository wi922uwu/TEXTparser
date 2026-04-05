import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadFiles } from '../../services/api';
import './FileUpload.css';

interface FileUploadProps {
  onUploadComplete: (uploads: Array<{ fileId: string; filename: string }>) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadComplete }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string>('');

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setUploading(true);
    setUploadProgress(`Загрузка ${acceptedFiles.length} файл(ов)...`);

    try {
      const results = await uploadFiles(acceptedFiles);

      const uploads = results.map(r => ({
        fileId: r.file_id,
        filename: r.filename,
      }));

      onUploadComplete(uploads);
      setUploadProgress('');
    } catch (error) {
      console.error('Upload error:', error);
      setUploadProgress('Ошибка загрузки файлов');
    } finally {
      setUploading(false);
    }
  }, [onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/tiff': ['.tiff', '.tif'],
    },
    maxSize: 5 * 1024 * 1024, // 5MB
    disabled: uploading,
  });

  return (
    <div className="file-upload">
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'disabled' : ''}`}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div className="upload-status">
            <div className="spinner"></div>
            <p>{uploadProgress}</p>
          </div>
        ) : isDragActive ? (
          <p>Отпустите файлы здесь...</p>
        ) : (
          <div className="upload-prompt">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p>Перетащите файлы сюда или нажмите для выбора</p>
            <p className="file-info">PDF, JPG, PNG, TIFF (макс. 5MB)</p>
          </div>
        )}
      </div>
    </div>
  );
};
