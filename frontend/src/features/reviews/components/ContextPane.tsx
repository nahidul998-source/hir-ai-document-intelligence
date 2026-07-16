import React from 'react';
import { useReviewStore } from '../../../../stores/reviewStore';
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
                    <div className="bg-white p-3 rounded-md border border-slate-200 shadow-sm space-y-2 text-xs">
                        <div className="flex justify-between">
                            <span className="text-slate-500">AI Confidence</span>
                            <span className="font-medium text-emerald-600">98.5%</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-slate-500">Master Data Match</span>
                            <span className="font-medium">Exact (BUY-001)</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-slate-500">Provider</span>
                            <span className="font-medium text-slate-700">Qwen 2.5 32B</span>
                        </div>
                    </div>
                </section>

                {/* Audit History */}
                <section>
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 mb-3 border-b pb-1 border-slate-200">
                        <History size={16} className="text-amber-500" /> Edit History
                    </div>
                    <div className="space-y-3">
                        <div className="relative pl-4 border-l-2 border-indigo-200">
                            <div className="absolute -left-[5px] top-1 w-2 h-2 rounded-full bg-indigo-500"></div>
                            <div className="text-[10px] text-slate-400 mb-0.5">10:45 AM - AI Extraction</div>
                            <div className="text-xs bg-white border border-slate-200 rounded p-2 text-slate-600 shadow-sm font-mono">
                                "Acme Corporation"
                            </div>
                        </div>
                        <div className="relative pl-4 border-l-2 border-slate-200">
                            <div className="absolute -left-[5px] top-1 w-2 h-2 rounded-full bg-slate-300"></div>
                            <div className="text-[10px] text-slate-400 mb-0.5">11:02 AM - Edited by User</div>
                            <div className="text-xs bg-amber-50 border border-amber-200 rounded p-2 text-slate-700 shadow-sm font-mono">
                                "Acme Corp Ltd"
                            </div>
                        </div>
                    </div>
                </section>

                {/* Comments */}
                <section>
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 mb-3 border-b pb-1 border-slate-200">
                        <MessageSquare size={16} className="text-emerald-500" /> Collaboration
                    </div>
                    <div className="bg-white p-3 rounded-md border border-slate-200 shadow-sm">
                        <div className="text-xs text-slate-500 italic text-center py-4">
                            No comments on this field yet.
                        </div>
                        <div className="mt-2 flex gap-2">
                            <input type="text" placeholder="Add note..." className="flex-1 text-xs border border-slate-300 rounded px-2 py-1.5 focus:ring-1 focus:ring-indigo-500 focus:outline-none" />
                            <button className="bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded text-xs font-medium hover:bg-indigo-100 transition-colors">Post</button>
                        </div>
                    </div>
                </section>

            </div>
        </div>
    );
};
