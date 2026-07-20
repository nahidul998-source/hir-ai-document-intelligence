import React from 'react';

interface Citation {
  document: string;
  page: number;
  section: string;
  confidence: number;
  bbox?: { x1: number, y1: number, x2: number, y2: number };
}

interface Props {
  citations: Citation[];
}

const RAGCitationViewer: React.FC<Props> = ({ citations }) => {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-4 pt-4 border-t border-gray-100">
      <h4 className="text-sm font-semibold text-gray-700 mb-3">Sources & Citations:</h4>
      <div className="flex flex-wrap gap-2">
        {citations.map((cite, idx) => (
          <button 
            key={idx}
            className="inline-flex items-center px-3 py-1.5 bg-blue-50 text-blue-700 text-xs font-medium rounded-full hover:bg-blue-100 transition border border-blue-200"
            title={`Confidence: ${(cite.confidence * 100).toFixed(0)}%`}
          >
            <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {cite.document} - Pg. {cite.page}
          </button>
        ))}
      </div>
    </div>
  );
};

export default RAGCitationViewer;
