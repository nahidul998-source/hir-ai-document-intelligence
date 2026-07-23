import React, { useState, useEffect } from 'react';
import { Target, AlertTriangle, Clock, CheckCircle } from 'lucide-react';
import { apiClient } from '../../../lib/api-client';

export const EvaluationDashboard: React.FC = () => {
    const [metrics, setMetrics] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                const res = await apiClient.get('/evaluation/metrics?days=30');
                setMetrics(res.data);
            } catch (error) {
                console.error("Failed to fetch evaluation metrics", error);
            } finally {
                setLoading(false);
            }
        };
        fetchMetrics();
    }, []);

    if (loading) {
        return <div className="p-8 text-center text-slate-500">Loading AI Evaluation Metrics...</div>;
    }

    if (!metrics) {
        return <div className="p-8 text-center text-red-500">Failed to load metrics.</div>;
    }

    return (
        <div className="p-6 bg-white rounded-lg shadow-sm border border-slate-200">
            <h2 className="text-lg font-semibold text-slate-800 mb-6 flex items-center gap-2">
                <Target size={20} className="text-indigo-600" />
                AI Evaluation Framework (Last {metrics.timeframe_days} Days)
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-4 rounded border border-slate-100 bg-slate-50">
                    <div className="flex items-center gap-2 text-slate-600 mb-2">
                        <CheckCircle size={16} className="text-emerald-500" />
                        <span className="text-sm font-medium">AI vs Human Agreement</span>
                    </div>
                    <div className="text-2xl font-bold text-slate-800">
                        {metrics.ai_human_agreement_percent}%
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Fields accepted without edits</p>
                </div>
                
                <div className="p-4 rounded border border-slate-100 bg-slate-50">
                    <div className="flex items-center gap-2 text-slate-600 mb-2">
                        <AlertTriangle size={16} className="text-amber-500" />
                        <span className="text-sm font-medium">Correction Rate</span>
                    </div>
                    <div className="text-2xl font-bold text-slate-800">
                        {metrics.correction_rate_percent}%
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Fields manually edited</p>
                </div>
                
                <div className="p-4 rounded border border-slate-100 bg-slate-50">
                    <div className="flex items-center gap-2 text-slate-600 mb-2">
                        <Target size={16} className="text-red-500" />
                        <span className="text-sm font-medium">Hallucination Proxy</span>
                    </div>
                    <div className="text-2xl font-bold text-slate-800">
                        {metrics.hallucination_rate_percent}%
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Fields outright rejected</p>
                </div>
                
                <div className="p-4 rounded border border-slate-100 bg-slate-50">
                    <div className="flex items-center gap-2 text-slate-600 mb-2">
                        <Clock size={16} className="text-blue-500" />
                        <span className="text-sm font-medium">Avg Review Time</span>
                    </div>
                    <div className="text-2xl font-bold text-slate-800">
                        {metrics.average_review_time_seconds}s
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Time to final approval</p>
                </div>
            </div>
        </div>
    );
};
