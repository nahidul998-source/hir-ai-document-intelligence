import { apiClient } from '../lib/api-client';

export interface OverviewMetrics {
  total_documents: number;
  completed_documents: number;
  review_pending_documents: number;
  failed_documents: number;
  ai_accuracy_pct: number;
  erp_success_rate_pct: number;
  sla_compliance_pct: number;
  total_tokens_consumed: number;
  estimated_ai_cost_usd: number;
}

export interface AccuracyAnalytics {
  overall_accuracy_pct: number;
  field_accuracy: Record<string, number>;
  document_type_accuracy: Record<string, number>;
}

export interface TokenProviderUsage {
  provider: string;
  model: string;
  tokens: number;
  cost_usd: number;
  share_pct: number;
}

export interface TokenCostMetrics {
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_cost_usd: number;
  providers: TokenProviderUsage[];
}

export interface QueueInfo {
  queue_name: string;
  messages_pending: number;
  messages_processed_per_min: number;
  status: string;
}

export interface WorkerInfo {
  worker_type: string;
  active_instances: number;
  avg_cpu_utilization_pct: number;
  status: string;
}

export interface OperationsStats {
  queues: QueueInfo[];
  workers: WorkerInfo[];
}

export interface ReviewerProductivity {
  avg_review_time_seconds: number;
  total_reviews_completed: number;
  field_correction_rate_pct: number;
  top_reviewers: { reviewer_name: string; reviews_count: number; avg_time_sec: number }[];
}

export interface CommercialAnalytics {
  buyers: { buyer_code: string; buyer_name: string; volume: number; accuracy_pct: number; avg_processing_time_sec: number }[];
  factories: { factory_code: string; factory_name: string; volume: number; accuracy_pct: number }[];
}

export const analyticsApi = {
  getOverview: async () => {
    const res = await apiClient.get<OverviewMetrics>('/analytics/overview');
    return res.data;
  },

  getAccuracy: async () => {
    const res = await apiClient.get<AccuracyAnalytics>('/analytics/accuracy');
    return res.data;
  },

  getConfidenceDistribution: async () => {
    const res = await apiClient.get<Record<string, number>>('/analytics/confidence-distribution');
    return res.data;
  },

  getTokenUsage: async () => {
    const res = await apiClient.get<TokenCostMetrics>('/analytics/token-usage');
    return res.data;
  },

  getOperations: async () => {
    const res = await apiClient.get<OperationsStats>('/analytics/operations');
    return res.data;
  },

  getReviewerProductivity: async () => {
    const res = await apiClient.get<ReviewerProductivity>('/analytics/reviewer-productivity');
    return res.data;
  },

  getBuyerFactory: async () => {
    const res = await apiClient.get<CommercialAnalytics>('/analytics/buyer-factory');
    return res.data;
  },

  exportReport: (format: 'csv' | 'excel' | 'pdf') => {
    return `/api/v1/analytics/export?format=${format}`;
  }
};
