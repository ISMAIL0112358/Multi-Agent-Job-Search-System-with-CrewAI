import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import client from '../api/client';
import './ResumeUpload.css';

export default function ResumeUpload({ conversationId, onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await client.post(
        `/conversations/${conversationId}/resume`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      onUploadComplete(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload resume');
    } finally {
      setUploading(false);
    }
  }, [conversationId, onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div className="resume-upload-wrapper animate-fade-in" id="resume-upload">
      <div
        {...getRootProps()}
        className={`resume-dropzone ${isDragActive ? 'dragging' : ''} ${uploading ? 'uploading' : ''}`}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div className="resume-upload-status">
            <div className="resume-upload-spinner" />
            <p>Extracting text from PDF...</p>
          </div>
        ) : (
          <>
            <div className="resume-upload-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="12" y1="18" x2="12" y2="12"/>
                <line x1="9" y1="15" x2="12" y2="12"/>
                <line x1="15" y1="15" x2="12" y2="12"/>
              </svg>
            </div>
            <p className="resume-upload-text">
              {isDragActive
                ? 'Drop your resume here...'
                : 'Drag & drop your resume PDF here'}
            </p>
            <span className="resume-upload-hint">or click to browse files</span>
          </>
        )}
      </div>
      {error && (
        <div className="resume-upload-error">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          {error}
        </div>
      )}
    </div>
  );
}
