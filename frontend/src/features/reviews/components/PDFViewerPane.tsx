import React, { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { useReviewStore, HighlightBox } from '../../../stores/reviewStore';
import { ZoomIn, ZoomOut, Maximize, RotateCw } from 'lucide-react';

// Setup PDF worker
pdfjs.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/5.4.296/pdf.worker.min.mjs';

interface PDFViewerPaneProps {
    docId: string;
}

export const PDFViewerPane: React.FC<PDFViewerPaneProps> = ({ docId }) => {
    const { activeField, zoomLevel, rotation, setZoomLevel, setRotation, highlights } = useReviewStore();
    const [numPages, setNumPages] = useState<number | null>(null);
    const [file, setFile] = useState<string | null>(null);
    const [isLoadingFile, setIsLoadingFile] = useState(true);
    const [fileError, setFileError] = useState<string | null>(null);

    useEffect(() => {
        let objectUrl: string | null = null;
        const fetchFile = async () => {
            setIsLoadingFile(true);
            setFileError(null);
            try {
                const token = localStorage.getItem('token');
                const response = await fetch(`http://localhost:8002/api/v1/documents/download/${docId}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                if (!response.ok) {
                    throw new Error('Failed to load document file from server');
                }
                const blob = await response.blob();
                objectUrl = URL.createObjectURL(blob);
                setFile(objectUrl);
            } catch (err: any) {
                console.error(err);
                setFileError(err.message || 'Error loading PDF');
            } finally {
                setIsLoadingFile(false);
            }
        };

        if (docId) {
            fetchFile();
        }

        return () => {
            if (objectUrl) {
                URL.revokeObjectURL(objectUrl);
            }
        };
    }, [docId]);

    function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
        setNumPages(numPages);
    }

    const handleZoomIn = () => setZoomLevel(zoomLevel + 0.25);
    const handleZoomOut = () => setZoomLevel(zoomLevel - 0.25);
    const handleRotate = () => setRotation((rotation + 90) % 360);

    return (
        <div className="flex flex-col h-full bg-slate-100">
            {/* Toolbar */}
            <div className="flex items-center justify-between p-3 bg-white border-b border-slate-200 shrink-0 shadow-sm">
                <div className="font-semibold text-slate-700 text-sm flex items-center gap-2">
                    <span className="bg-indigo-100 text-indigo-700 px-2 py-1 rounded text-xs">PDF</span>
                    Document Viewer
                </div>
                <div className="flex items-center gap-1 bg-slate-50 p-1 rounded-md border border-slate-200">
                    <button onClick={handleZoomOut} className="p-1.5 hover:bg-slate-200 rounded text-slate-600 transition-colors" title="Zoom Out">
                        <ZoomOut size={16} />
                    </button>
                    <span className="text-xs font-medium w-12 text-center text-slate-600">{Math.round(zoomLevel * 100)}%</span>
                    <button onClick={handleZoomIn} className="p-1.5 hover:bg-slate-200 rounded text-slate-600 transition-colors" title="Zoom In">
                        <ZoomIn size={16} />
                    </button>
                    <div className="w-px h-4 bg-slate-300 mx-1"></div>
                    <button onClick={handleRotate} className="p-1.5 hover:bg-slate-200 rounded text-slate-600 transition-colors" title="Rotate">
                        <RotateCw size={16} />
                    </button>
                    <button className="p-1.5 hover:bg-slate-200 rounded text-slate-600 transition-colors" title="Fit to Screen">
                        <Maximize size={16} />
                    </button>
                </div>
            </div>

            {/* Viewer Canvas */}
            <div className="flex-1 overflow-auto relative p-4 custom-scrollbar bg-slate-200/50 flex justify-center">
                {isLoadingFile ? (
                    <div className="flex items-center justify-center h-full text-slate-400 m-auto">
                        <span className="animate-pulse">Fetching PDF from storage...</span>
                    </div>
                ) : fileError ? (
                    <div className="text-red-500 m-auto flex flex-col items-center gap-2">
                        <span>Failed to load PDF file.</span>
                        <span className="text-xs text-slate-500">{fileError}</span>
                    </div>
                ) : file ? (
                    <Document
                        file={file}
                        onLoadSuccess={onDocumentLoadSuccess}
                        className="flex flex-col items-center gap-4"
                        loading={
                            <div className="flex items-center justify-center h-full text-slate-400">
                                <span className="animate-pulse">Loading PDF...</span>
                            </div>
                        }
                    >
                        {Array.from(new Array(numPages), (_, index) => (
                            <div key={`page_${index + 1}`} className="relative shadow-lg ring-1 ring-slate-900/5">
                                <Page 
                                    pageNumber={index + 1} 
                                    scale={zoomLevel} 
                                    rotate={rotation}
                                    renderAnnotationLayer={true}
                                    renderTextLayer={true}
                                    className="bg-white"
                                />
                                {/* Bounding Box Overlays */}
                                {highlights
                                    .filter((h: HighlightBox) => h.page === index + 1)
                                    .map((h: HighlightBox) => {
                                        const isActive = h.field_name === activeField;
                                        return (
                                            <div
                                                key={h.id}
                                                className={`absolute transition-all duration-200 cursor-pointer ${
                                                    isActive 
                                                        ? 'bg-amber-300/40 border-2 border-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.5)] z-20' 
                                                        : 'bg-indigo-300/20 border border-indigo-400 hover:bg-indigo-300/40 z-10'
                                                }`}
                                                style={{
                                                    left: `${h.x * zoomLevel}px`,
                                                    top: `${h.y * zoomLevel}px`,
                                                    width: `${h.width * zoomLevel}px`,
                                                    height: `${h.height * zoomLevel}px`,
                                                }}
                                                title={`Field: ${h.field_name}`}
                                            />
                                        );
                                })}
                            </div>
                        ))}
                    </Document>
                ) : (
                    <div className="text-slate-400 m-auto">No document selected.</div>
                )}
            </div>
        </div>
    );
};
