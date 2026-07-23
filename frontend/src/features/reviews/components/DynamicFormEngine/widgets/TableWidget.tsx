import React from 'react';
import { ERPTable } from './ERPTable';

export const TableWidget = ({ fieldSchema }: { fieldSchema: any }) => {
    return (
        <div className="mt-4">
            <ERPTable fieldSchema={fieldSchema} />
        </div>
    );
};
