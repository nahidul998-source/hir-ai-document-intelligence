import axios from 'axios';

// Assuming an axios instance is usually defined, we'll just use a basic one or look for it
// For now, let's use standard fetch or a simple axios setup.
const API_BASE = 'http://localhost:8002/api/v1';

export const fetchDocumentSchema = async (documentType: string) => {
    const response = await axios.get(`${API_BASE}/schemas/documents/${documentType}`);
    return response.data;
};
