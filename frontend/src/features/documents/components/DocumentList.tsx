import React, { useState, useEffect } from 'react';
import { apiClient } from '../../../lib/api-client';

interface Document {
  id: string;
  filename: string;
  file_type: string;
  current_version: number;
  status: string;
  created_at: string;
}

interface DocumentListProps {
  documents: Document[];
  onReviewDocument?: (docId: string) => void;
  onProcessDocument?: (docId: string, providerKey?: string) => void;
  onDeleteDocument?: (docId: string) => void;
}

export const DocumentList: React.FC<DocumentListProps> = ({ documents, onReviewDocument, onProcessDocument, onDeleteDocument }) => {
  const [providers, setProviders] = useState<{key: string, name: string}[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');

  useEffect(() => {
    const fetchProviders = async () => {
      try {
        const response = await apiClient.get('/monitoring/providers');
        setProviders(response.data);
      } catch (err) {
        console.error('Failed to fetch providers', err);
      }
    };
    fetchProviders();
  }, []);

  const handlePreview = async (docId: string) => {
    try {
      const response = await apiClient.get(`/documents/download/${docId}`, {
        responseType: 'blob'
      });
      const blobUrl = URL.createObjectURL(response.data);
      window.open(blobUrl, '_blank');
    } catch (error) {
      console.error("Failed to preview document:", error);
      alert("Failed to load document preview.");
    }
  };
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'processing': return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      case 'review_pending': return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
      case 'completed': return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'failed': return 'bg-red-500/10 text-red-500 border-red-500/20';
      default: return 'bg-slate-500/10 text-slate-500 border-slate-500/20';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
        <h3 className="text-base font-bold text-slate-100">Document Queue</h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Force AI Provider:</span>
          <select 
            className="text-xs bg-slate-950 border border-slate-800 text-slate-300 rounded px-2 py-1 outline-none"
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
          >
            <option value="">Auto (Orchestrator)</option>
            {providers.map(p => (
              <option key={p.key} value={p.key}>{p.name}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950 text-xs uppercase text-slate-400">
            <tr>
              <th className="px-6 py-3">Filename</th>
              <th className="px-6 py-3">Type</th>
              <th className="px-6 py-3">Version</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Uploaded At</th>
              <th className="px-6 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {documents.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-slate-500 italic">
                  No documents uploaded to this project yet.
                </td>
              </tr>
            ) : (
              documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-slate-950/30 transition-colors">
                  <td className="px-6 py-4 font-semibold text-slate-200">{doc.filename}</td>
                  <td className="px-6 py-4 text-xs text-slate-400">{doc.file_type}</td>
                  <td className="px-6 py-4 text-slate-400">v{doc.current_version}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${getStatusColor(doc.status)}`}>
                      {doc.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-400">
                    {new Date(doc.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right flex items-center justify-end gap-2">
                    {doc.status === 'review_pending' && (
                      <button
                        onClick={() => onReviewDocument?.(doc.id)}
                        className="px-3 py-1.5 text-xs font-semibold bg-violet-600 hover:bg-violet-700 text-white rounded transition-colors"
                      >
                        Review
                      </button>
                    )}
                    {(doc.status === 'pending' || doc.status === 'failed' || doc.status === 'processing') && (
                      <button
                        onClick={() => onProcessDocument?.(doc.id, selectedProvider || undefined)}
                        className="px-3 py-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                      >
                        Process
                      </button>
                    )}
                    <button
                      onClick={() => handlePreview(doc.id)}
                      className="px-3 py-1.5 text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white rounded transition-colors"
                    >
                      Preview
                    </button>
                    <button
                      onClick={() => onDeleteDocument?.(doc.id)}
                      className="px-3 py-1.5 text-xs font-semibold bg-red-600 hover:bg-red-700 text-white rounded transition-colors"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
