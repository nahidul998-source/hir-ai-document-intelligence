import React, { useState, useEffect } from 'react';
import { apiClient } from '../../../lib/api-client';
import { Shield, Search, ChevronLeft, ChevronRight, Eye, EyeOff } from 'lucide-react';

interface AuditLogEntry {
  id: string;
  created_at: string;
  action: string;
  user_id: string | null;
  details: Record<string, any>;
  ip_address: string | null;
}

export const AuditDashboard: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [limit] = useState(15);
  const [actionQuery, setActionQuery] = useState('');
  const [searchTrigger, setSearchTrigger] = useState(0);
  const [loading, setLoading] = useState(true);
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const url = `/monitoring/audit-logs?skip=${skip}&limit=${limit}${actionQuery ? `&action=${actionQuery}` : ''}`;
      const response = await apiClient.get(url);
      setLogs(response.data.logs);
      setTotal(response.data.total);
    } catch (err) {
      console.error('Audit logs fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [skip, searchTrigger]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSkip(0);
    setSearchTrigger(prev => prev + 1);
  };

  const toggleExpandLog = (id: string) => {
    if (expandedLogId === id) {
      setExpandedLogId(null);
    } else {
      setExpandedLogId(id);
    }
  };

  const handlePrevPage = () => {
    if (skip >= limit) {
      setSkip(prev => prev - limit);
    }
  };

  const handleNextPage = () => {
    if (skip + limit < total) {
      setSkip(prev => prev + limit);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <Shield className="w-6 h-6 text-violet-500" />
          Security Audit Explorer
        </h2>
        <p className="text-slate-400 text-sm mt-1">Immutable tracking of user modifications, uploads, reviews, and platform configuration events.</p>
      </div>

      {/* Filter and Search Controls */}
      <form onSubmit={handleSearchSubmit} className="flex gap-4 items-center bg-slate-900/40 p-4 border border-slate-800 rounded-xl">
        <div className="flex-1 relative">
          <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500">
            <Search className="w-4 h-4" />
          </span>
          <input
            type="text"
            placeholder="Search by action type (e.g. UPLOAD_DOCUMENT, START_REVIEW)..."
            value={actionQuery}
            onChange={(e) => setActionQuery(e.target.value)}
            className="w-full bg-slate-950 text-slate-300 text-sm border border-slate-800 rounded-lg pl-9 pr-4 py-2 focus:outline-none focus:border-violet-500 transition-colors"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="bg-violet-650 hover:bg-violet-600 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2 rounded-lg transition-all"
        >
          Search
        </button>
      </form>

      {/* Logs Table */}
      <div className="bg-slate-900/30 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-12 text-slate-500 space-y-2">
            <div className="w-6 h-6 border-2 border-violet-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-xs">Fetching system records...</span>
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            No audit records found matching your filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/20 text-slate-400 font-semibold uppercase">
                  <th className="py-3.5 px-6">Timestamp</th>
                  <th className="py-3.5 px-6">Action</th>
                  <th className="py-3.5 px-6">Actor ID</th>
                  <th className="py-3.5 px-6">IP Address</th>
                  <th className="py-3.5 px-6 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850">
                {logs.map((log) => (
                  <React.Fragment key={log.id}>
                    <tr className="hover:bg-slate-900/10 text-slate-300 transition-colors">
                      <td className="py-4 px-6 text-slate-400 font-mono">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="py-4 px-6">
                        <span className="px-2 py-0.5 rounded font-mono font-bold text-xs bg-slate-850/80 border border-slate-800 text-slate-200">
                          {log.action}
                        </span>
                      </td>
                      <td className="py-4 px-6 font-mono text-slate-400">
                        {log.user_id ? log.user_id.substring(0, 13) + '...' : 'System'}
                      </td>
                      <td className="py-4 px-6 font-mono text-slate-500">
                        {log.ip_address || '127.0.0.1'}
                      </td>
                      <td className="py-4 px-6 text-right">
                        <button
                          onClick={() => toggleExpandLog(log.id)}
                          className="text-violet-400 hover:text-violet-300 inline-flex items-center gap-1.5 font-semibold"
                        >
                          {expandedLogId === log.id ? (
                            <>
                              <EyeOff className="w-3.5 h-3.5" />
                              Hide
                            </>
                          ) : (
                            <>
                              <Eye className="w-3.5 h-3.5" />
                              Inspect
                            </>
                          )}
                        </button>
                      </td>
                    </tr>

                    {/* Expandable JSON payload panel */}
                    {expandedLogId === log.id && (
                      <tr>
                        <td colSpan={5} className="bg-slate-950/65 px-6 py-4 border-t border-slate-850">
                          <div className="space-y-2">
                            <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500">
                              System Action Parameters
                            </div>
                            <pre className="text-[11px] font-mono text-violet-300 bg-slate-950 p-4 border border-slate-900 rounded-lg overflow-x-auto max-w-full">
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        {total > 0 && (
          <div className="px-6 py-4 bg-slate-900/20 border-t border-slate-800 flex items-center justify-between">
            <span className="text-xs text-slate-500">
              Showing <span className="font-semibold text-slate-400">{skip + 1}</span> to{' '}
              <span className="font-semibold text-slate-400">{Math.min(skip + limit, total)}</span> of{' '}
              <span className="font-semibold text-slate-400">{total}</span> logs
            </span>
            
            <div className="flex items-center gap-2">
              <button
                onClick={handlePrevPage}
                disabled={skip === 0 || loading}
                className="p-1.5 bg-slate-900 text-slate-400 hover:text-slate-350 disabled:opacity-40 border border-slate-800 rounded transition-all"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={handleNextPage}
                disabled={skip + limit >= total || loading}
                className="p-1.5 bg-slate-900 text-slate-400 hover:text-slate-350 disabled:opacity-40 border border-slate-800 rounded transition-all"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
