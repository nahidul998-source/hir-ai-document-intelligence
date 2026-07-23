import React from 'react';
import { useFormContext, Controller } from 'react-hook-form';
import { useReviewStore } from '../../../../../stores/reviewStore';
import { CheckCircle2 } from 'lucide-react';

export const TextWidget = ({ fieldSchema }: { fieldSchema: any }) => {
    const { control } = useFormContext();
    const { activeField, setActiveField } = useReviewStore();
    const { name, ui } = fieldSchema;

    const isActive = activeField === name;
    const baseClasses = `w-full rounded-md border text-sm transition-all focus:ring-2 focus:outline-none p-2.5`;
    const dynamicClasses = isActive 
        ? 'border-indigo-500 ring-indigo-200 bg-indigo-50/30' 
        : 'border-slate-300 hover:border-slate-400 focus:border-indigo-500 bg-white';

    return (
        <div className="relative group mb-4">
            <label className="block text-xs font-medium text-slate-700 mb-1">
                {ui.label} {ui.required && <span className="text-red-500">*</span>}
            </label>
            <div className="relative">
                <Controller
                    name={name}
                    control={control}
                    render={({ field }) => (
                        <input 
                            {...field} 
                            placeholder={ui.placeholder}
                            className={`${baseClasses} ${dynamicClasses}`}
                            onFocus={() => setActiveField(name)}
                        />
                    )}
                />
                {/* Simulated Validation Badge */}
                {fieldSchema.erp_mapping && (
                    <div className="absolute right-2 top-2.5 flex items-center text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded text-[10px] font-medium border border-emerald-200">
                        <CheckCircle2 size={12} className="mr-1" /> ERP Mapped
                    </div>
                )}
            </div>
        </div>
    );
};
