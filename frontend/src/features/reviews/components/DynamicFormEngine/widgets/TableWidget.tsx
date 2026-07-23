import React from 'react';
import { ERPTable } from './ERPTable';
import { FieldSchema } from '../types';

export const TableWidget = React.memo(({ fieldSchema }: { fieldSchema: FieldSchema }) => {
    return (
        <div className="mt-4">
            <ERPTable fieldSchema={fieldSchema} />
        </div>
    );
});
