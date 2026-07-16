import { useForm, Controller } from 'react-hook-form';
import { useReviewStore } from '../../../../stores/reviewStore';
import { CheckCircle2, AlertTriangle, Info, Save } from 'lucide-react';
import { RequirePermission } from '../../auth/components/RequirePermission';

interface MockFormValues {
    buyer_name: string;
    style_code: string;
    total_quantity: number;
    order_lines: Array<{
        color: string;
        size: string;
        quantity: number;
    }>;
}

export const ERPFormPane: React.FC = () => {
    const { activeField, setActiveField, setUnsavedChanges } = useReviewStore();
    const [isSaving, setIsSaving] = useState(false);
    
    const { control, handleSubmit, watch, formState: { isDirty } } = useForm<MockFormValues>({
        defaultValues: {
            buyer_name: 'Acme Corporation',
            style_code: 'FW26-001',
            total_quantity: 1000,
            order_lines: [
                { color: 'Black', size: 'M', quantity: 500 },
                { color: 'Navy', size: 'L', quantity: 500 }
            ]
        }
    });

    useEffect(() => {
        setUnsavedChanges(isDirty);
    }, [isDirty, setUnsavedChanges]);

    // Simulated Auto-Save Debounce
    useEffect(() => {
        const subscription = watch((value, { name, type }) => {
            if (type === 'change') {
                setIsSaving(true);
                const timer = setTimeout(() => {
                    console.log('Auto-saved draft field:', name, value);
                    setIsSaving(false);
                }, 800);
                return () => clearTimeout(timer);
            }
        });
        return () => subscription.unsubscribe();
    }, [watch]);

    const handleFocus = (fieldName: string) => {
        setActiveField(fieldName);
    };

    const getFieldClasses = (fieldName: string) => {
        const isActive = activeField === fieldName;
        return `w-full rounded-md border text-sm transition-all focus:ring-2 focus:outline-none ${
            isActive 
                ? 'border-indigo-500 ring-indigo-200 bg-indigo-50/30' 
                : 'border-slate-300 hover:border-slate-400 focus:border-indigo-500 bg-white'
        } p-2.5`;
    };

    return (
        <div className="flex flex-col h-full bg-white relative">
            {/* Header */}
            <div className="flex items-center justify-between p-3 bg-white border-b border-slate-200 shrink-0 sticky top-0 z-10 shadow-sm">
                <div className="font-semibold text-slate-700 text-sm flex items-center gap-2">
                    <span className="bg-emerald-100 text-emerald-700 px-2 py-1 rounded text-xs">Form</span>
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
                    {/* Buyer Section */}
                    <section className="bg-slate-50 p-4 rounded-lg border border-slate-100 shadow-sm">
                        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4 border-b pb-2">Header Information</h3>
                        <div className="space-y-4">
                            
                            {/* Buyer Name */}
                            <div className="relative group">
                                <label className="block text-xs font-medium text-slate-700 mb-1">
                                    Buyer Name
                                </label>
                                <div className="relative">
                                    <Controller
                                        name="buyer_name"
                                        control={control}
                                        render={({ field }) => (
                                            <input 
                                                {...field} 
                                                className={getFieldClasses('buyer_name')}
                                                onFocus={() => handleFocus('buyer_name')}
                                            />
                                        )}
                                    />
                                    {/* Master Data Match Badge */}
                                    <div className="absolute right-2 top-2.5 flex items-center text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded text-[10px] font-medium border border-emerald-200" title="Matched ERP Master Data: BUY-001">
                                        <CheckCircle2 size={12} className="mr-1" /> ERP Linked
                                    </div>
                                </div>
                            </div>

                            {/* Style Code */}
                            <div className="relative group">
                                <label className="block text-xs font-medium text-slate-700 mb-1">
                                    Style Code <span className="text-red-500">*</span>
                                </label>
                                <Controller
                                    name="style_code"
                                    control={control}
                                    render={({ field }) => (
                                        <input 
                                            {...field} 
                                            className={getFieldClasses('style_code')}
                                            onFocus={() => handleFocus('style_code')}
                                        />
                                    )}
                                />
                            </div>
                        </div>
                    </section>

                    {/* Order Lines Section (Simulating Dynamic Array) */}
                    <section className="bg-slate-50 p-4 rounded-lg border border-slate-100 shadow-sm">
                        <div className="flex items-center justify-between border-b pb-2 mb-4">
                            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Order Breakdowns</h3>
                            
                            <div className="flex items-center text-red-600 bg-red-50 px-2 py-1 rounded-md text-xs font-medium border border-red-200">
                                <AlertTriangle size={14} className="mr-1.5" /> Quantity Math Error
                            </div>
                        </div>
                        
                        <div className="space-y-4">
                            {/* Line 1 */}
                            <div className="grid grid-cols-3 gap-3 p-3 bg-white rounded border border-slate-200 hover:border-indigo-300 transition-colors">
                                <div>
                                    <label className="block text-[10px] text-slate-500 mb-1 uppercase">Color</label>
                                    <input defaultValue="Black" className={getFieldClasses('lines.0.color')} onFocus={() => handleFocus('lines.0.color')} />
                                </div>
                                <div>
                                    <label className="block text-[10px] text-slate-500 mb-1 uppercase">Size</label>
                                    <input defaultValue="M" className={getFieldClasses('lines.0.size')} onFocus={() => handleFocus('lines.0.size')} />
                                </div>
                                <div>
                                    <label className="block text-[10px] text-slate-500 mb-1 uppercase">Quantity</label>
                                    <input defaultValue="500" type="number" className={`${getFieldClasses('lines.0.quantity')} border-red-300 bg-red-50 focus:ring-red-200`} onFocus={() => handleFocus('lines.0.quantity')} />
                                </div>
                            </div>
                        </div>
                    </section>
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
                    <button className="px-5 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 shadow-sm transition-all focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1 flex items-center gap-2">
                        Approve & Push to ERP
                    </button>
                </RequirePermission>
            </div>
        </div>
    );
};
