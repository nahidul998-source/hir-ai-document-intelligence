import { apiClient } from '../lib/api-client';

export interface AdminUser {
  id: string;
  email: string;
  is_active: boolean;
  role_id: string;
  created_at: string | null;
}

export interface AdminRole {
  id: string;
  name: string;
  permissions: Record<string, boolean> | string[];
}

export interface Tenant {
  id: string;
  name: string;
  code: string;
  status: string;
  max_users: number;
  storage_quota_gb: number;
}

export interface FeatureFlag {
  id: string;
  key: string;
  description: string | null;
  is_enabled: boolean;
}

export interface ValidationRule {
  id: string;
  field_name: string;
  rule_type: string;
  constraint_value: string;
  error_message: string;
  is_enabled: boolean;
}

export interface SystemConfig {
  id: string;
  key: string;
  value: string;
  category: string;
  description: string | null;
}

export interface ApiKeyData {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  is_active: boolean;
  expires_at: string | null;
  raw_api_key?: string;
}

export interface AIProvider {
  key: string;
  name: string;
  enabled: boolean;
  api_url: string;
  model_name: string;
  priority_index: number;
  status: string;
  latency: number;
  p95_latency: number;
  requests: number;
  errors: number;
  success_rate: number;
  failure_rate: number;
  retry_count: number;
  fallback_count: number;
  timeout_count: number;
  last_successful_request: string | null;
  last_error: any;
  last_health_check: string | null;
  capabilities: {
    context_length: number;
    json_mode: boolean;
    vision: boolean;
    streaming: boolean;
  };
}

export interface AIRoutingRule {
  document_type: string;
  provider_keys: string[];
}

export const adminApi = {
  getAIProviders: async () => {
    const res = await apiClient.get<{ providers: AIProvider[], priority: string[] }>('/ai-providers');
    return res.data;
  },
  
  testAIProvider: async (key: string) => {
    const res = await apiClient.post<{ healthy: boolean }>(`/ai-providers/${key}/test`);
    return res.data;
  },
  
  toggleAIProvider: async (key: string) => {
    const res = await apiClient.post<{ status: string, enabled: boolean }>(`/ai-providers/${key}/toggle`);
    return res.data;
  },
  
  updateAIProviderPriority: async (priority: string[]) => {
    const res = await apiClient.post<{ status: string, priority: string[] }>('/ai-providers/priority', { priority });
    return res.data;
  },
  
  getAIProviderModels: async (key: string) => {
    const res = await apiClient.get<any>(`/ai-providers/${key}/models`);
    return res.data;
  },

  getAIRoutingRules: async () => {
    const res = await apiClient.get<AIRoutingRule[]>('/ai-providers/routing');
    return res.data;
  },

  updateAIRoutingRule: async (documentType: string, providerKeys: string[]) => {
    const res = await apiClient.post<{ status: string }>('/ai-providers/routing', {
      document_type: documentType,
      provider_keys: providerKeys
    });
    return res.data;
  },
  getUsers: async () => {
    const res = await apiClient.get<AdminUser[]>('/admin/users');
    return res.data;
  },

  getRoles: async () => {
    const res = await apiClient.get<AdminRole[]>('/admin/roles');
    return res.data;
  },

  getTenants: async () => {
    const res = await apiClient.get<Tenant[]>('/admin/tenants');
    return res.data;
  },

  createTenant: async (payload: { name: string; code: string; max_users?: number; storage_quota_gb?: number }) => {
    const res = await apiClient.post<Tenant>('/admin/tenants', payload);
    return res.data;
  },

  getFeatureFlags: async () => {
    const res = await apiClient.get<FeatureFlag[]>('/admin/feature-flags');
    return res.data;
  },

  setFeatureFlag: async (payload: { key: string; is_enabled: boolean; description?: string }) => {
    const res = await apiClient.post<FeatureFlag>('/admin/feature-flags', payload);
    return res.data;
  },

  getValidationRules: async () => {
    const res = await apiClient.get<ValidationRule[]>('/admin/validation-rules');
    return res.data;
  },

  saveValidationRule: async (payload: { field_name: string; rule_type: string; constraint_value: string; error_message: string; is_enabled?: boolean }) => {
    const res = await apiClient.post<ValidationRule>('/admin/validation-rules', payload);
    return res.data;
  },

  getSystemConfigs: async () => {
    const res = await apiClient.get<SystemConfig[]>('/admin/system-config');
    return res.data;
  },

  setSystemConfig: async (payload: { key: string; value: string; category?: string; description?: string }) => {
    const res = await apiClient.post<SystemConfig>('/admin/system-config', payload);
    return res.data;
  },

  getApiKeys: async () => {
    const res = await apiClient.get<ApiKeyData[]>('/admin/api-keys');
    return res.data;
  },

  createApiKey: async (payload: { name: string; scopes?: string[]; expire_days?: number }) => {
    const res = await apiClient.post<ApiKeyData>('/admin/api-keys', payload);
    return res.data;
  },

  revokeApiKey: async (keyId: string) => {
    const res = await apiClient.delete<{ status: string }>(`/admin/api-keys/${keyId}`);
    return res.data;
  },

  purgeQueue: async (queueName: string) => {
    const res = await apiClient.post(`/admin/queues/${queueName}/purge`);
    return res.data;
  },

  triggerBackup: async () => {
    const res = await apiClient.post('/admin/backups/trigger');
    return res.data;
  }
};
