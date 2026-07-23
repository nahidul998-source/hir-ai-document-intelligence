import React, { useMemo } from 'react';
import { useFormContext, useFieldArray } from 'react-hook-form';
import {
    useReactTable,
    getCoreRowModel,
    flexRender,
    createColumnHelper,
} from '@tanstack/react-table';

export const ERPTable = ({ fieldSchema }: { fieldSchema: any }) => {
    const { control, register } = useFormContext();
    const { name, ui, items } = fieldSchema;

    const { fields, append } = useFieldArray({
        control,
        name: name
    });

    // In case no items exist, ensure there is at least one empty row
    React.useEffect(() => {
        if (fields.length === 0) {
            append({});
        }
    }, [fields.length, append]);

    const columnHelper = createColumnHelper<any>();

    const columns = useMemo(() => {
        if (!items || !items.properties) return [];

        return items.properties.map((prop: any) => {
            return columnHelper.accessor(prop.name, {
                header: () => prop.ui?.label || prop.name,
                cell: (info) => {
                    const rowIndex = info.row.index;
                    const fieldName = `${name}.${rowIndex}.${prop.name}`;
                    return (
                        <input
                            {...register(fieldName)}
                            className="w-full h-full bg-transparent outline-none p-2 border-b border-transparent focus:border-indigo-400 text-sm"
                            placeholder={`Enter ${prop.ui?.label || prop.name}`}
                        />
                    );
                }
            });
        });
    }, [items, name, register, columnHelper]);

    const table = useReactTable({
        data: fields,
        columns,
        getCoreRowModel: getCoreRowModel(),
    });

    return (
        <div className="w-full border rounded-lg overflow-hidden bg-white shadow-sm mt-2 mb-4">
            <div className="bg-slate-100 p-3 border-b text-sm font-semibold flex justify-between items-center">
                <span>{ui.label}</span>
                <button
                    type="button"
                    onClick={() => append({})}
                    className="text-xs bg-indigo-50 text-indigo-700 px-3 py-1 rounded hover:bg-indigo-100"
                >
                    + Add Row
                </button>
            </div>
            
            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-max">
                    <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b">
                        {table.getHeaderGroups().map(headerGroup => (
                            <tr key={headerGroup.id}>
                                {headerGroup.headers.map(header => (
                                    <th key={header.id} className="p-3 font-semibold border-r last:border-r-0">
                                        {flexRender(
                                            header.column.columnDef.header,
                                            header.getContext()
                                        )}
                                    </th>
                                ))}
                            </tr>
                        ))}
                    </thead>
                    <tbody className="divide-y text-sm text-slate-700">
                        {table.getRowModel().rows.map(row => (
                            <tr key={row.id} className="hover:bg-slate-50/50 group">
                                {row.getVisibleCells().map(cell => (
                                    <td key={cell.id} className="border-r last:border-r-0 p-0 relative">
                                        {flexRender(
                                            cell.column.columnDef.cell,
                                            cell.getContext()
                                        )}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            
            {fields.length === 0 && (
                <div className="p-6 text-center text-slate-400 text-sm">
                    No rows available.
                </div>
            )}
        </div>
    );
};
