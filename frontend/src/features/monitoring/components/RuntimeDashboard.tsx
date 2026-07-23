import React, { useState, useEffect } from 'react';
import { Play, CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import { apiClient } from '../../../lib/api-client';

export const RuntimeDashboard: React.FC = () => {
    const [documents, setDocuments] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchDocuments = async () => {
        try {
            const res = await apiClient.get('/monitoring/documents');
            setDocuments(res.data.documents || []);
        } catch (error) {
            console.error('Failed to fetch documents status', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDocuments();
        const interval = setInterval(fetchDocuments, 5000);
        return () => clearInterval(interval);
    }, []);

    const getStatusIcon = (status: string) => {
        switch(status) {
            case 'completed':
            case 'approved':
                return <CheckCircle className="text-emerald-500" size={16} />;
            case 'failed':
            case 'error':
                return <AlertTriangle className="text-red-500" size={16} />;
            case 'review_pending':
                return <Clock className="text-amber-500" size={16} />;
            default:
                return <Play className="text-indigo-500 animate-pulse" size={16} />;
        }
    };

    if (loading) {
        return <div className="p-8 text-center text-slate-500">Loading Pipeline Monitor...</div>;
    }

    return (
        <div className="p-6 bg-white rounded-lg shadow-sm border border-slate-200">
            <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
                <Play size={20} className="text-indigo-600" />
                Pipeline Runtime Monitor
            </h2>
            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="bg-slate-50 text-slate-600 font-medium border-b border-slate-200">
                        <tr>
                            <th className="px-4 py-3">Document ID</th>
                            <th className="px-4 py-3">Filename</th>
                            <th className="px-4 py-3">Type</th>
                            <th className="px-4 py-3">Status</th>
                            <th className="px-4 py-3">Last Updated</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {documents.map(doc => (
                            <tr key={doc.id} className="hover:bg-slate-50/50">
                                <td className="px-4 py-3 font-mono text-xs text-slate-500">{doc.id}</td>
                                <td className="px-4 py-3 font-medium text-slate-700">{doc.filename}</td>
                                <td className="px-4 py-3 text-slate-600">
                                    <span className="bg-slate-100 px-2 py-1 rounded text-xs">
                                        {doc.document_type || 'Unknown'}
                                    </span>
                                </td>
                                <td className="px-4 py-3 flex items-center gap-2 font-medium capitalize">
                                    {getStatusIcon(doc.status)}
                                    {doc.status.replace('_', ' ')}
                                </td>
                                <td className="px-4 py-3 text-slate-500 text-xs">
                                    {new Date(doc.updated_at).toLocaleString()}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
