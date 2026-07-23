export interface FieldUI {
    label: string;
    placeholder?: string;
    required?: boolean;
    widget?: string;
    width?: string;
    options?: { label: string; value: string }[];
}

export interface FieldSchema {
    name: string;
    type: string;
    ui: FieldUI;
    erp_mapping?: string;
    items?: {
        type: string;
        properties: FieldSchema[];
    };
}

export interface ModuleSchema {
    id: string;
    title: string;
    fields: FieldSchema[];
}

export interface DocumentSchema {
    schema_id: string;
    version: string;
    document_type: string;
    modules: ModuleSchema[];
}
