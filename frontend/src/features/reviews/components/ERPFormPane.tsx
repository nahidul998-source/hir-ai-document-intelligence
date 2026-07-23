import React, { useState, useEffect } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { useReviewStore } from '../../../stores/reviewStore';
import { CheckCircle2, Save } from 'lucide-react';
import { RequirePermission } from '../../auth/components/RequirePermission';
import { fetchDocumentSchema } from '../../../api/schemasApi';
import { SchemaRenderer } from './DynamicFormEngine/SchemaRenderer';
import { ErrorBoundary } from '../../../lib/ErrorBoundary';

export const ERPFormPane: React.FC<{ docId: string }> = ({ docId }) => {
    const { setUnsavedChanges } = useReviewStore();
    const [isSaving, setIsSaving] = useState(false);
    const [schema, setSchema] = useState<any>(null);
    const [isLoadingSchema, setIsLoadingSchema] = useState(true);
    const [sessionData, setSessionData] = useState<any>(null);

    const methods = useForm({
        defaultValues: {}
    });

    const { watch, formState: { isDirty }, reset } = methods;

    useEffect(() => {
        const loadSessionAndSchema = async () => {
            try {
                // Fetch Review Session Data
                const { apiClient } = await import('../../../lib/api-client');
                const sessionRes = await apiClient.get(`/documents/${docId}/review`);
                const session = sessionRes.data;
                setSessionData(session);
                
                // Initialize form with extracted fields
                if (session.fields) {
                    reset(session.fields);
                }
                
                if (session.highlights) {
                    useReviewStore.getState().setHighlights(session.highlights);
                }

                // Fetch Schema based on document type
                const fetchedSchema = await fetchDocumentSchema(session.document_type || "tech_pack");
                setSchema(fetchedSchema);
            } catch (error) {
                console.error("Failed to fetch session or schema", error);
            } finally {
                setIsLoadingSchema(false);
            }
        };
        if (docId) {
            loadSessionAndSchema();
        }
    }, [docId, reset]);

    useEffect(() => {
        setUnsavedChanges(isDirty);
    }, [isDirty, setUnsavedChanges]);

    // Simulated Auto-Save Debounce
    useEffect(() => {
        let timer: ReturnType<typeof setTimeout> | null = null;
        const subscription = watch(async (value, { name, type }) => {
            if (type === 'change' && name && sessionData) {
                setIsSaving(true);
                if (timer) clearTimeout(timer);
                timer = setTimeout(async () => {
                    try {
                        const { apiClient } = await import('../../../lib/api-client');
                        const fieldValue = (value as any)[name];
                        await apiClient.patch(`/documents/${docId}/review/fields/${name}`, {
                            session_id: sessionData.session_id,
                            edited_value: fieldValue
                        });
                        console.log('Draft saved to backend:', name);
                    } catch (error) {
                        console.error('Failed to save draft:', error);
                    } finally {
                        setIsSaving(false);
                    }
                }, 800);
            }
        });
        return () => {
            subscription.unsubscribe();
            if (timer) clearTimeout(timer);
        };
    }, [watch, sessionData, docId]);

    const handleApprove = async () => {
        if (!sessionData) return;
        try {
            const { apiClient } = await import('../../../lib/api-client');
            await apiClient.post(`/documents/${docId}/review/approve`, {
                session_id: sessionData.session_id
            });
            alert('Document approved and pushed to ERP pipeline!');
        } catch (error) {
            console.error('Failed to approve document', error);
            alert('Failed to approve document.');
        }
    };

    return (
        <FormProvider {...methods}>
            <div className="flex flex-col h-full bg-white relative">
                {/* Header */}
                <div className="flex items-center justify-between p-3 bg-white border-b border-slate-200 shrink-0 sticky top-0 z-10 shadow-sm">
                    <div className="font-semibold text-slate-700 text-sm flex items-center gap-2">
                        <span className="bg-emerald-100 text-emerald-700 px-2 py-1 rounded text-xs">Dynamic Form</span>
                        Data Extraction
                    </div>
                    <div className="flex items-center gap-3">
                        {isSaving ? (
                            <span className="text-xs text-amber-600 flex items-center gap-1 animate-pulse">
                                <Save size={14} /> Saving draft...
                            </span>
                        ) : isDirty ? (
                            <span className="text-xs text-slate-400 flex items-center gap-1">
                                <Save size={14} /> Unsaved changes
                            </span>
                        ) : (
                            <span className="text-xs text-emerald-600 flex items-center gap-1">
                                <CheckCircle2 size={14} /> Saved
                            </span>
                        )}
                    </div>
                </div>

                {/* Form Scroll Area */}
                <div className="flex-1 overflow-y-auto p-5 custom-scrollbar">
                    <form className="space-y-6">
                        {isLoadingSchema ? (
                            <div className="p-8 text-center text-slate-500 animate-pulse">Loading Schema definitions...</div>
                        ) : schema ? (
                            <ErrorBoundary fallback={<div className="p-4 text-red-500 bg-red-50 rounded">Failed to render schema form. Check schema validity.</div>}>
                                <SchemaRenderer schema={schema} />
                            </ErrorBoundary>
                        ) : (
                            <div className="p-8 text-center text-red-500">Error loading schema</div>
                        )}
                    </form>
                </div>
                
                {/* Sticky Action Footer */}
                <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-end gap-3 shrink-0">
                    <RequirePermission permission="review:write">
                        <button className="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-300 rounded-md hover:bg-slate-100 transition-colors">
                            Reject
                        </button>
                    </RequirePermission>
                    
                    <RequirePermission permission="review:approve" fallback={
                        <button disabled className="px-5 py-2 text-sm font-medium text-white bg-indigo-300 rounded-md cursor-not-allowed">
                            Approve (Locked)
                        </button>
                    }>
                        <button onClick={handleApprove} className="px-5 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 shadow-sm transition-all focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1 flex items-center gap-2">
                            Approve & Push to ERP
                        </button>
                    </RequirePermission>
                </div>
            </div>
        </FormProvider>
    );
};
