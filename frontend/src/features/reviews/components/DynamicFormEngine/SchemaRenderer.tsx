import React from 'react';
import { getWidget } from './WidgetRegistry';

export const SchemaRenderer = ({ schema }: { schema: any }) => {
    if (!schema || !schema.modules) return <div className="p-4 text-slate-500">Loading Schema...</div>;

    return (
        <div className="space-y-6">
            {schema.modules.map((mod: any) => (
                <section key={mod.module_id} className="bg-slate-50 p-4 rounded-lg border border-slate-100 shadow-sm">
                    <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4 border-b pb-2">
                        {mod.title}
                    </h3>
                    <div className="space-y-4">
                        {mod.fields.map((field: any) => {
                            const Widget = getWidget(field.ui.ui_widget);
                            return <Widget key={field.name} fieldSchema={field} />;
                        })}
                    </div>
                </section>
            ))}
        </div>
    );
};
