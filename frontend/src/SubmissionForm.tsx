import React, { useState, useRef, useCallback } from 'react';
import { getSessionToken, BACKEND_URL } from './utils/auth';

interface Props {
  userId: string;
}

type SetStatus = React.Dispatch<React.SetStateAction<string | null>>;

function setErrorStatus(setStatus: SetStatus, exception: Error) {
  console.error(exception);
  setStatus(`❌ Upload failed: ${exception.message}`);
}

async function hashFile(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getFileIcon(fileType: string): string {
  if (fileType.includes('pdf')) return '📄';
  if (fileType.includes('image')) return '🖼️';
  if (fileType.includes('text') || fileType.includes('html') || fileType.includes('md')) return '📝';
  if (fileType.includes('word') || fileType.includes('document')) return '📄';
  return '📁';
}

function SubmissionForm({ userId }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [submissionId, setSubmissionId] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length > 0) {
      const droppedFile = droppedFiles[0];
      // Check if file type is accepted
      const acceptedTypes = ['.txt', '.pdf', '.jpg', '.jpeg', '.png', '.docx', '.doc', '.rtf', '.html', '.htm', '.md'];
      const fileExtension = '.' + droppedFile.name.split('.').pop()?.toLowerCase();

      if (acceptedTypes.includes(fileExtension)) {
        setFile(droppedFile);
        setStatus(null);
        setSubmissionId(null);
      } else {
        setStatus('❌ File type not supported. Please upload a supported file type.');
      }
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setStatus(null);
      setSubmissionId(null);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Reset state for new submission
    setStatus(null);
    setSubmissionId(null);
    setUploadProgress(0);

    if (!file) {
      setStatus('❌ Please select a file to upload.');
      return;
    }

    setIsUploading(true);

    try {
      setStatus('🔍 Processing file...');
      setUploadProgress(10);

      const fileHash = await hashFile(file);
      setUploadProgress(20);

      const auth_token = await getSessionToken();
      if (!auth_token) {
        setIsUploading(false);
        return setErrorStatus(setStatus, new Error('Not logged in or unable to retrieve authentication token'));
      }

      // Check if API Gateway URL is defined
      if (!BACKEND_URL) {
        setIsUploading(false);
        return setErrorStatus(setStatus, new Error('Backend URL is not defined'));
      }

      setStatus('🔗 Preparing upload...');
      setUploadProgress(40);

      // Add 'Bearer ' prefix to the token
      const response = await fetch(BACKEND_URL + '/generate-upload-url', {
        method: 'POST',
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${auth_token}`,
        },
        body: JSON.stringify({
          user_id: userId,
          file_name: file.name,
          file_hash: fileHash,
        }),
      });

      // Log the full response for debugging
      console.log("API Response status:", response.status);
      console.log("API Response headers:", response.headers);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("API Error Response:", errorText);
        setIsUploading(false);
        return setErrorStatus(
          setStatus,
          new Error(`Failed to get upload URL: ${response.status} ${response.statusText}`)
        );
      }

      const data = await response.json();
      console.log("API Response data:", data);

      const { upload_url, submission_id } = data;
      const contentType = file.type || 'application/octet-stream';

      setStatus('📤 Uploading to cloud...');
      setUploadProgress(60);

      const uploadResult = await fetch(upload_url, {
        method: 'PUT',
        headers: {
          'Content-Type': contentType,
        },
        body: file,
      });

      if (!uploadResult.ok) {
        setIsUploading(false);
        return setErrorStatus(setStatus, new Error(`Upload to cloud failed: ${uploadResult.statusText}`));
      }

      setUploadProgress(100);
      setStatus(`✅ Upload successful! Your file has been processed.`);
      setSubmissionId(submission_id);
    } catch (err: any) {
      setErrorStatus(setStatus, err);
    } finally {
      setIsUploading(false);
    }
  };

  const removeFile = () => {
    setFile(null);
    setStatus(null);
    setSubmissionId(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="submission-form-container">
      <div className="upload-section">
        <h3 className="upload-title">Upload Learning Material</h3>
        <p className="upload-description">
          Upload documents, images, or text files to extract vocabulary and create learning materials.
        </p>

        <div className="supported-formats">
          <span className="format-label">Supported formats:</span>
          <span className="format-tags">
            <span className="format-tag">PDF</span>
            <span className="format-tag">DOCX</span>
            <span className="format-tag">TXT</span>
            <span className="format-tag">Images</span>
            <span className="format-tag">HTML</span>
          </span>
        </div>

        <form onSubmit={handleSubmit} className="upload-form">
          <div
            className={`file-drop-zone ${isDragOver ? 'drag-over' : ''} ${file ? 'has-file' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.pdf,.jpg,.jpeg,.png,.docx,.doc,.rtf,.html,.htm,.md"
              onChange={handleFileSelect}
              className="file-input"
            />

            {!file ? (
              <div className="drop-zone-content">
                <div className="upload-icon">📁</div>
                <h4>Drop your file here</h4>
                <p>or click to browse</p>
                <div className="file-size-limit">Maximum file size: 50MB</div>
              </div>
            ) : (
              <div className="selected-file">
                <div className="file-info">
                  <span className="file-icon">{getFileIcon(file.type)}</span>
                  <div className="file-details">
                    <div className="file-name">{file.name}</div>
                    <div className="file-size">{formatFileSize(file.size)}</div>
                  </div>
                </div>
                <button
                  type="button"
                  className="remove-file-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile();
                  }}
                >
                  ✕
                </button>
              </div>
            )}
          </div>

          {isUploading && (
            <div className="upload-progress">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <div className="progress-text">{uploadProgress}%</div>
            </div>
          )}

          <button
            type="submit"
            disabled={!file || isUploading}
            className={`upload-button ${!file || isUploading ? 'disabled' : ''}`}
          >
            {isUploading ? 'Uploading...' : 'Upload & Process'}
          </button>
        </form>

        {status && (
          <div className={`status-message ${status.includes('❌') ? 'error' : status.includes('✅') ? 'success' : 'info'}`}>
            {status}
          </div>
        )}

        {submissionId && (
          <div className="success-actions">
            <a href="/submissions" className="view-submissions-link">
              📋 View All Submissions
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

export default SubmissionForm;
