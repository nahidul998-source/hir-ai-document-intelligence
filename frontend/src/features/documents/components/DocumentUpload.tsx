import React, { useState, useRef } from 'react';
import { apiClient } from '../../../lib/api-client';

interface DocumentUploadProps {
  projectId: string;
  onUploadSuccess: () => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ projectId, onUploadSuccess }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      await apiClient.post(`/documents/upload/${projectId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      onUploadSuccess();
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to upload document.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="p-6 bg-slate-900 border border-slate-800 rounded-xl space-y-4">
      <div>
        <h3 className="text-base font-bold text-slate-100">Upload Documents</h3>
        <p className="text-xs text-slate-400">Order Sheets, Tech Packs, Purchase Orders, etc.</p>
      </div>

      {uploadError && (
        <div className="p-3 text-xs text-red-400 bg-red-950/40 border border-red-900/50 rounded-lg">
          {uploadError}
        </div>
      )}

      <div className="border-2 border-dashed border-slate-800 hover:border-brand-500/50 rounded-lg p-8 flex flex-col items-center justify-center cursor-pointer transition-colors relative">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          disabled={isUploading}
          className="absolute inset-0 opacity-0 cursor-pointer disabled:cursor-not-allowed"
          accept=".pdf,.png,.jpg,.jpeg,.csv,.xlsx"
        />
        <div className="text-center space-y-2">
          <p className="text-sm font-semibold text-slate-300">
            {isUploading ? 'Uploading file...' : 'Click to browse or drop file here'}
          </p>
          <p className="text-xs text-slate-500">PDF, XLS, CSV, Image up to 50MB</p>
        </div>
      </div>
    </div>
  );
};
