import React from 'react';

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
}

export const DocumentList: React.FC<DocumentListProps> = ({ documents }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'processing': return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      case 'completed': return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'failed': return 'bg-red-500/10 text-red-500 border-red-500/20';
      default: return 'bg-slate-500/10 text-slate-500 border-slate-500/20';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-800">
        <h3 className="text-base font-bold text-slate-100">Document Queue</h3>
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
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {documents.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-slate-500 italic">
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
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
