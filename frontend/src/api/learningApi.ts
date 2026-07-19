import { apiClient } from '../lib/api-client';

export interface LearningCorrectionRecord {
  id: string;
  document_id: string;
  session_id: string;
  field_name: string;
  original_extracted_value: string | null;
  corrected_value: string | null;
  was_modified: boolean;
  initial_confidence: number | null;
  source_page: number | null;
  created_at: string | null;
}

export interface LearningDataset {
  id: string;
  name: string;
  description: string;
  dataset_type: string;
  sample_count: number;
  status: string;
  created_at: string | null;
}

export interface ConfidenceAnalyticsData {
  sample_size: number;
  calibration_bins: Record<string, {
    total: number;
    corrections: number;
    accepted: number;
    acceptance_rate: number;
    correction_rate: number;
  }>;
  recommended_auto_approve_threshold: number;
}

export interface ReviewerProductivityData {
  reviewer_id: string;
  total_reviewed: number;
  total_modified: number;
  modification_rate: number;
  avg_review_seconds: number;
}

export interface ExtractionQualityReportData {
  overall_accuracy: number;
  total_extractions_reviewed: number;
  total_corrections_made: number;
  field_accuracy_breakdown: Record<string, {
    total: number;
    corrections: number;
    accuracy_rate: number;
  }>;
  dataset_readiness: {
    available_samples: number;
    ready_for_fine_tuning: boolean;
  };
}

export const learningApi = {
  getCorrections: async (skip = 0, limit = 50) => {
    const res = await apiClient.get<{ total: number; records: LearningCorrectionRecord[] }>(`/learning/corrections?skip=${skip}&limit=${limit}`);
    return res.data;
  },

  getDatasets: async () => {
    const res = await apiClient.get<LearningDataset[]>('/learning/datasets');
    return res.data;
  },

  createDataset: async (payload: { name: string; description?: string; dataset_type?: string; min_confidence_threshold?: number; only_modified?: boolean }) => {
    const res = await apiClient.post<{ id: string; name: string; sample_count: number }>('/learning/datasets', payload);
    return res.data;
  },

  exportDataset: async (datasetId: string, format = 'jsonl') => {
    const res = await apiClient.get<string>(`/learning/datasets/${datasetId}/export?format=${format}`, {
      responseType: 'text'
    });
    return res.data;
  },

  getExemplars: async (fieldName?: string) => {
    const res = await apiClient.get(`/learning/prompts/exemplars${fieldName ? `?field_name=${fieldName}` : ''}`);
    return res.data;
  },

  getConfidenceAnalytics: async () => {
    const res = await apiClient.get<ConfidenceAnalyticsData>('/learning/analytics/confidence');
    return res.data;
  },

  getReviewerAnalytics: async () => {
    const res = await apiClient.get<ReviewerProductivityData[]>('/learning/analytics/reviewers');
    return res.data;
  },

  getQualityReport: async () => {
    const res = await apiClient.get<ExtractionQualityReportData>('/learning/reports/quality');
    return res.data;
  }
};
