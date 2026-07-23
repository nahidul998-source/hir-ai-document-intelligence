import { TextWidget } from './widgets/TextWidget';
import { TableWidget } from './widgets/TableWidget';

export const WidgetRegistry: Record<string, React.FC<any>> = {
    'text': TextWidget,
    'number': TextWidget, // Fallback for now
    'table': TableWidget,
};

export const getWidget = (uiWidget: string) => {
    return WidgetRegistry[uiWidget] || TextWidget; // default to text
};
