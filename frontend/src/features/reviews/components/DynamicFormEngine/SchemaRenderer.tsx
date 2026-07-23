import React from 'react';
import { getWidget } from './WidgetRegistry';
import { DocumentSchema, ModuleSchema, FieldSchema } from './types';

export const SchemaRenderer = React.memo(({ schema }: { schema: DocumentSchema }) => {
    if (!schema || !schema.modules) return <div className="p-4 text-slate-500">Loading Schema...</div>;

    return (
        <div className="space-y-6">
            {schema.modules.map((mod: ModuleSchema) => (
                <section key={mod.id} className="bg-slate-50 p-4 rounded-lg border border-slate-100 shadow-sm">
                    <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4 border-b pb-2">
                        {mod.title}
                    </h3>
                    <div className="space-y-4">
                        {mod.fields.map((field: FieldSchema) => {
                            const Widget = getWidget(field.ui.ui_widget);
                            return <Widget key={field.name} fieldSchema={field} />;
                        })}
                    </div>
                </section>
            ))}
        </div>
    );
});
