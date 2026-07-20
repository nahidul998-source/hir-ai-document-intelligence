import React, { useEffect } from 'react';
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from 'react-resizable-panels';
import { PDFViewerPane } from './PDFViewerPane';
import { ERPFormPane } from './ERPFormPane';
import { ContextPane } from './ContextPane';
interface ReviewWorkspaceProps {
    docId: string;
}

export const ReviewWorkspace: React.FC<ReviewWorkspaceProps> = ({ docId }) => {
    // We bind hotkeys globally at the workspace level (or app level)
    // using a dedicated hook or event listeners.

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                console.log("Draft saved (mock)!");
                // Trigger debounced save
            }
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                console.log("Document approved (mock)!");
                // Trigger approval mutation
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    return (
        <div className="flex h-[calc(100vh-4rem)] w-full bg-slate-50 overflow-hidden text-slate-900">
            <PanelGroup orientation="horizontal" id="hir-workspace-layout">
                {/* Left Pane - PDF Viewer */}
                <Panel defaultSize={35} minSize={20} className="bg-white border-r border-slate-200 flex flex-col shadow-sm z-10">
                    <PDFViewerPane docId={docId} />
                </Panel>
                
                <PanelResizeHandle className="w-1.5 bg-slate-200 hover:bg-indigo-400 transition-colors cursor-col-resize active:bg-indigo-600" />
                
                {/* Center Pane - ERP Form */}
                <Panel defaultSize={40} minSize={25} className="bg-white border-r border-slate-200 flex flex-col z-0">
                    <ERPFormPane />
                </Panel>

                <PanelResizeHandle className="w-1.5 bg-slate-200 hover:bg-indigo-400 transition-colors cursor-col-resize active:bg-indigo-600" />
                
                {/* Right Pane - Context */}
                <Panel defaultSize={25} minSize={15} className="bg-slate-50 flex flex-col shadow-inner z-0">
                    <ContextPane />
                </Panel>
            </PanelGroup>
        </div>
    );
};
