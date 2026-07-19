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

export const adminApi = {
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
