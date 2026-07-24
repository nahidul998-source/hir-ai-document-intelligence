import React from 'react';
import { useReviewStore } from '../../../stores/reviewStore';
import { ShieldAlert, History, MessageSquare, Bot } from 'lucide-react';

export const ContextPane: React.FC = () => {
    const { activeField } = useReviewStore();

    return (
        <div className="flex flex-col h-full bg-slate-50 text-slate-800 border-l border-slate-200">
            {/* Header */}
            <div className="flex items-center justify-between p-3 bg-white border-b border-slate-200 shrink-0 shadow-sm">
                <div className="font-semibold text-slate-700 text-sm flex items-center gap-2">
                    <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">Context</span>
                    Field Inspector
                </div>
            </div>

            {/* Active Field Display */}
            <div className="p-4 bg-indigo-900 text-white shrink-0 shadow-md relative overflow-hidden">
                <div className="absolute top-0 right-0 p-8 opacity-10">
                    <Bot size={100} />
                </div>
                <div className="relative z-10">
                    <h2 className="text-xs font-semibold text-indigo-300 uppercase tracking-widest mb-1">Target</h2>
                    <div className="text-lg font-mono font-bold break-all">
                        {activeField || "None Selected"}
                    </div>
                </div>
            </div>

            {/* Scrollable Context Area */}
            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar space-y-6">
                
                {/* AI Metadata */}
                <section>
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 mb-3 border-b pb-1 border-slate-200">
                        <ShieldAlert size={16} className="text-indigo-500" /> Validation Trace
                    </div>
                    {activeField ? (
                        <div className="bg-white p-3 rounded-md border border-slate-200 shadow-sm space-y-2 text-xs">
                            <div className="flex justify-between">
                                <span className="text-slate-500">AI Confidence</span>
                                <span className="font-medium text-slate-700">-</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-500">Master Data Match</span>
                                <span className="font-medium text-slate-700">-</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-500">Provider</span>
                                <span className="font-medium text-slate-700">-</span>
                            </div>
                        </div>
                    ) : (
                        <div className="text-xs text-slate-500 italic text-center py-4 bg-white p-3 rounded-md border border-slate-200 shadow-sm">
                            Select a field to view validation trace.
                        </div>
                    )}
                </section>

                {/* Audit History */}
                <section>
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 mb-3 border-b pb-1 border-slate-200">
                        <History size={16} className="text-amber-500" /> Edit History
                    </div>
                    {activeField ? (
                        <div className="text-xs text-slate-500 italic text-center py-4 bg-white p-3 rounded-md border border-slate-200 shadow-sm">
                            No edit history available for this field.
                        </div>
                    ) : (
                        <div className="text-xs text-slate-500 italic text-center py-4 bg-white p-3 rounded-md border border-slate-200 shadow-sm">
                            Select a field to view edit history.
                        </div>
                    )}
                </section>

                {/* Comments */}
                <section>
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 mb-3 border-b pb-1 border-slate-200">
                        <MessageSquare size={16} className="text-emerald-500" /> Collaboration
                    </div>
                    <div className="bg-white p-3 rounded-md border border-slate-200 shadow-sm">
                        <div className="text-xs text-slate-500 italic text-center py-4">
                            {activeField ? "No comments on this field yet." : "Select a field to view comments."}
                        </div>
                        {activeField && (
                            <div className="mt-2 flex gap-2">
                                <input disabled type="text" placeholder="Add note..." className="flex-1 text-xs border border-slate-300 rounded px-2 py-1.5 focus:ring-1 focus:ring-indigo-500 focus:outline-none bg-slate-50 cursor-not-allowed" />
                                <button disabled className="bg-slate-100 text-slate-400 px-3 py-1.5 rounded text-xs font-medium cursor-not-allowed">Post</button>
                            </div>
                        )}
                    </div>
                </section>

            </div>
        </div>
    );
};
