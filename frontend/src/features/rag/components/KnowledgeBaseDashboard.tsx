import React, { useState } from 'react';

const KnowledgeBaseDashboard: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    setIsSearching(true);
    // Simulated API call to RAG hybrid search
    setTimeout(() => {
      setResults([
        {
          id: 'chunk-1',
          document: 'Nike Tech Pack Q3',
          page: 5,
          section: 'Sleeve Construction',
          confidence: 0.94,
          text: 'The sleeve must be double stitched at the seam.'
        }
      ]);
      setIsSearching(false);
    }, 800);
  };

  return (
    <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Enterprise Knowledge Base</h2>
      
      <div className="flex space-x-4 mb-8">
        <input 
          type="text" 
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="Search semantic knowledge (e.g., 'What is the tolerance for armhole seams?')"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button 
          onClick={handleSearch}
          disabled={isSearching}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
        >
          {isSearching ? 'Searching...' : 'Search'}
        </button>
      </div>

      <div className="space-y-4">
        {results.map((result, idx) => (
          <div key={idx} className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition">
            <div className="flex justify-between items-start mb-2">
              <h3 className="text-lg font-semibold text-gray-800">{result.document}</h3>
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                Confidence: {(result.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <p className="text-sm text-gray-500 mb-2">Page {result.page} • Section: {result.section}</p>
            <p className="text-gray-700 bg-gray-50 p-3 rounded">{result.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default KnowledgeBaseDashboard;
