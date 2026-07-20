import React, { useEffect, useState } from 'react';
import {
  adminApi,
  AdminUser,
  Tenant,
  FeatureFlag,
  SystemConfig,
  ApiKeyData,
  AIProvider,
  AIRoutingRule
} from '../../../api/adminApi';
import {
  Shield,
  Users,
  Building2,
  Key,
  ToggleLeft,
  ToggleRight,
  Plus,
  RefreshCw,
  HardDrive,
  Trash2,
  Cpu,
  Server,
  ArrowUp,
  ArrowDown,
  Activity,
  Layers,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<'users' | 'tenants' | 'flags' | 'keys' | 'ops' | 'providers'>('users');
  const [loading, setLoading] = useState(true);

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [configs, setConfigs] = useState<SystemConfig[]>([]);
  const [apiKeys, setApiKeys] = useState<ApiKeyData[]>([]);
  
  const [aiProviders, setAiProviders] = useState<AIProvider[]>([]);
  const [aiPriority, setAiPriority] = useState<string[]>([]);
  const [aiRoutingRules, setAiRoutingRules] = useState<AIRoutingRule[]>([]);

  // New Tenant Modal State
  const [tenantName, setTenantName] = useState('');
  const [tenantCode, setTenantCode] = useState('');

  // New Api Key Modal State
  const [keyName, setKeyName] = useState('');
  const [createdRawKey, setCreatedRawKey] = useState<string | null>(null);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [uRes, tRes, fRes, cfgRes, kRes, aiRes, routeRes] = await Promise.all([
        adminApi.getUsers(),
        adminApi.getTenants(),
        adminApi.getFeatureFlags(),
        adminApi.getSystemConfigs(),
        adminApi.getApiKeys(),
        adminApi.getAIProviders(),
        adminApi.getAIRoutingRules()
      ]);

      setUsers(uRes || []);
      setTenants(tRes || []);
      setFlags(fRes || []);
      setConfigs(cfgRes || []);
      setApiKeys(kRes || []);
      setAiRoutingRules(routeRes || []);
      
      if (aiRes) {
        setAiProviders(aiRes.providers || []);
        setAiPriority(aiRes.priority || []);
      }
    } catch (err) {
      console.error('Failed to load admin portal data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAdminData();
  }, []);

  const handleToggleFlag = async (key: string, currentStatus: boolean) => {
    try {
      await adminApi.setFeatureFlag({ key, is_enabled: !currentStatus });
      await loadAdminData();
    } catch (err) {
      console.error('Failed to toggle feature flag', err);
    }
  };

  const handleCreateTenant = async () => {
    if (!tenantName || !tenantCode) return;
    try {
      await adminApi.createTenant({ name: tenantName, code: tenantCode });
      setTenantName('');
      setTenantCode('');
      await loadAdminData();
    } catch (err) {
      console.error('Failed to create tenant', err);
    }
  };

  const handleCreateApiKey = async () => {
    if (!keyName) return;
    try {
      const res = await adminApi.createApiKey({ name: keyName });
      setCreatedRawKey(res.raw_api_key || null);
      setKeyName('');
      await loadAdminData();
    } catch (err) {
      console.error('Failed to create API key', err);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    try {
      await adminApi.revokeApiKey(keyId);
      await loadAdminData();
    } catch (err) {
      console.error('Failed to revoke key', err);
    }
  };

  const handleTriggerBackup = async () => {
    try {
      await adminApi.triggerBackup();
      alert('System Backup Snapshot Completed!');
      await loadAdminData();
    } catch (err) {
      console.error('Backup trigger failed', err);
    }
  };

  const handleTestProvider = async (key: string) => {
    try {
      const res = await adminApi.testAIProvider(key);
      alert(`Provider ${key} connection is ${res.healthy ? 'Successful (Healthy)' : 'Failed (Unhealthy)'}`);
      await loadAdminData();
    } catch (err) {
      console.error('Failed to test provider', err);
      alert('Error connecting to provider.');
    }
  };

  const handleToggleProvider = async (key: string) => {
    try {
      await adminApi.toggleAIProvider(key);
      await loadAdminData();
    } catch (err) {
      console.error('Failed to toggle provider', err);
    }
  };

  const handleMovePriority = async (key: string, direction: 'up' | 'down') => {
    const currentIndex = aiPriority.indexOf(key);
    if (currentIndex === -1) return;
    
    const newPriority = [...aiPriority];
    if (direction === 'up' && currentIndex > 0) {
      [newPriority[currentIndex - 1], newPriority[currentIndex]] = [newPriority[currentIndex], newPriority[currentIndex - 1]];
    } else if (direction === 'down' && currentIndex < newPriority.length - 1) {
      [newPriority[currentIndex + 1], newPriority[currentIndex]] = [newPriority[currentIndex], newPriority[currentIndex + 1]];
    } else {
      return;
    }
    
    try {
      await adminApi.updateAIProviderPriority(newPriority);
      await loadAdminData();
    } catch (err) {
      console.error('Failed to update priority', err);
    }
  };

  const handleReloadModels = async (key: string) => {
    try {
      const res = await adminApi.getAIProviderModels(key);
      console.log('Available models:', res);
      alert(`Models fetched successfully. Check console for details. Data: ${JSON.stringify(res).substring(0, 100)}...`);
    } catch (err) {
      console.error('Failed to reload models', err);
      alert('Error fetching models from provider.');
    }
  };

  const handleUpdateRoutingRule = async (docType: string, keys: string[]) => {
    try {
      await adminApi.updateAIRoutingRule(docType, keys);
      await loadAdminData();
    } catch (err) {
      console.error('Failed to update routing rule', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] text-slate-400">
        <RefreshCw className="animate-spin mr-2" size={20} />
        Loading Enterprise Administration Console...
      </div>
    );
  }

  return (
    <div className="space-y-6 text-slate-100">
      {/* Top Banner */}
      <div className="flex items-center justify-between bg-slate-900/60 p-6 rounded-xl border border-slate-800">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <Shield className="text-violet-400" size={28} />
            Enterprise Administration Portal
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Global User Management, Multi-Tenant Organizations, Dynamic Feature Toggles, API Keys & Operations Control
          </p>
        </div>
        <button
          onClick={loadAdminData}
          className="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 flex items-center gap-2 transition-colors"
        >
          <RefreshCw size={14} /> Refresh Admin Console
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-slate-800 flex gap-4 text-sm font-semibold">
        <button
          onClick={() => setActiveSubTab('users')}
          className={`pb-3 px-1 transition-colors border-b-2 flex items-center gap-2 ${
            activeSubTab === 'users' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Users size={16} /> Users & Roles ({users.length})
        </button>
        <button
          onClick={() => setActiveSubTab('tenants')}
          className={`pb-3 px-1 transition-colors border-b-2 flex items-center gap-2 ${
            activeSubTab === 'tenants' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Building2 size={16} /> Tenants & Quotas ({tenants.length})
        </button>
        <button
          onClick={() => setActiveSubTab('flags')}
          className={`pb-3 px-1 transition-colors border-b-2 flex items-center gap-2 ${
            activeSubTab === 'flags' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Cpu size={16} /> Feature Flags & Configs
        </button>
        <button
          onClick={() => setActiveSubTab('keys')}
          className={`pb-3 px-1 transition-colors border-b-2 flex items-center gap-2 ${
            activeSubTab === 'keys' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Key size={16} /> API Key Management ({apiKeys.length})
        </button>
        <button
          onClick={() => setActiveSubTab('providers')}
          className={`pb-3 px-1 transition-colors border-b-2 flex items-center gap-2 ${
            activeSubTab === 'providers' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Server size={16} /> AI Providers
        </button>
        <button
          onClick={() => setActiveSubTab('ops')}
          className={`pb-3 px-1 transition-colors border-b-2 flex items-center gap-2 ${
            activeSubTab === 'ops' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <HardDrive size={16} /> Ops & Backup Controls
        </button>
      </div>

      {/* Tab 1: Users & Roles */}
      {activeSubTab === 'users' && (
        <div className="space-y-6">
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-base font-semibold text-white">Platform Users</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/60 uppercase text-slate-400 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="p-3">Email</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Role ID</th>
                    <th className="p-3">Created At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-800/40">
                      <td className="p-3 font-medium text-slate-100">{u.email}</td>
                      <td className="p-3">
                        {u.is_active ? (
                          <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px]">Active</span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-300 text-[10px]">Disabled</span>
                        )}
                      </td>
                      <td className="p-3 font-mono text-slate-400">{u.role_id}</td>
                      <td className="p-3 text-slate-500">{u.created_at ? new Date(u.created_at).toLocaleString() : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Tenants */}
      {activeSubTab === 'tenants' && (
        <div className="space-y-6">
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 flex items-end gap-4">
            <div className="flex-1">
              <label className="block text-xs font-medium text-slate-300 mb-1">Organization Name</label>
              <input
                type="text"
                value={tenantName}
                onChange={(e) => setTenantName(e.target.value)}
                placeholder="e.g. Apex Garment Factory Ltd"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-100 focus:outline-none focus:border-violet-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Tenant Code</label>
              <input
                type="text"
                value={tenantCode}
                onChange={(e) => setTenantCode(e.target.value)}
                placeholder="APEX_01"
                className="bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-100 focus:outline-none focus:border-violet-500"
              />
            </div>
            <button
              onClick={handleCreateTenant}
              disabled={!tenantName || !tenantCode}
              className="px-4 py-2.5 text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              <Plus size={14} /> Add Tenant
            </button>
          </div>

          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-base font-semibold text-white">Registered Multi-Tenant Organizations</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {tenants.map((t) => (
                <div key={t.id} className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-100 text-sm">{t.name}</span>
                    <span className="px-2 py-0.5 text-[10px] rounded bg-emerald-500/20 text-emerald-300 uppercase font-bold">{t.status}</span>
                  </div>
                  <div className="text-xs text-slate-400">Code: <code className="text-slate-200">{t.code}</code></div>
                  <div className="flex justify-between text-xs text-slate-500 pt-2 border-t border-slate-900">
                    <span>Max Users: <strong>{t.max_users}</strong></span>
                    <span>Quota: <strong>{t.storage_quota_gb} GB</strong></span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Feature Flags & Configs */}
      {activeSubTab === 'flags' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-base font-semibold text-white">Dynamic Feature Flags</h3>
            <div className="space-y-3">
              {flags.map((f) => (
                <div key={f.id} className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-slate-200 text-xs">{f.key}</div>
                    <div className="text-[11px] text-slate-500">{f.description || 'System feature flag'}</div>
                  </div>
                  <button
                    onClick={() => handleToggleFlag(f.key, f.is_enabled)}
                    className="p-1 text-slate-300 hover:text-white transition-colors"
                  >
                    {f.is_enabled ? (
                      <ToggleRight className="text-emerald-400" size={28} />
                    ) : (
                      <ToggleLeft className="text-slate-600" size={28} />
                    )}
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-base font-semibold text-white">System Settings</h3>
            <div className="space-y-3">
              {configs.map((c) => (
                <div key={c.id} className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs space-y-1">
                  <div className="flex justify-between font-semibold text-slate-200">
                    <span>{c.key}</span>
                    <span className="text-violet-400 font-mono">{c.value}</span>
                  </div>
                  <p className="text-[11px] text-slate-500">{c.description || 'Global configuration setting'}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: API Keys */}
      {activeSubTab === 'keys' && (
        <div className="space-y-6">
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 flex items-end gap-4">
            <div className="flex-1">
              <label className="block text-xs font-medium text-slate-300 mb-1">API Key Description</label>
              <input
                type="text"
                value={keyName}
                onChange={(e) => setKeyName(e.target.value)}
                placeholder="e.g. ERP Integration Pipeline Key"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-100 focus:outline-none focus:border-violet-500"
              />
            </div>
            <button
              onClick={handleCreateApiKey}
              disabled={!keyName}
              className="px-4 py-2.5 text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              <Plus size={14} /> Generate API Key
            </button>
          </div>

          {createdRawKey && (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl space-y-2">
              <div className="text-xs font-bold text-emerald-400">New API Key Generated! Copy immediately (will not be shown again):</div>
              <div className="p-3 bg-slate-950 rounded border border-emerald-500/20 text-xs font-mono text-emerald-300 select-all">{createdRawKey}</div>
            </div>
          )}

          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-base font-semibold text-white">Active System API Keys</h3>
            <div className="space-y-3">
              {apiKeys.map((k) => (
                <div key={k.id} className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-slate-200">{k.name}</div>
                    <div className="text-slate-500 font-mono">Prefix: {k.key_prefix}...</div>
                  </div>
                  <div className="flex items-center gap-4">
                    {k.is_active ? (
                      <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px]">Active</span>
                    ) : (
                      <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-300 text-[10px]">Revoked</span>
                    )}
                    {k.is_active && (
                      <button
                        onClick={() => handleRevokeKey(k.id)}
                        className="px-2.5 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded text-[11px] transition-colors flex items-center gap-1"
                      >
                        <Trash2 size={12} /> Revoke Key
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: AI Providers */}
      {activeSubTab === 'providers' && (
        <div className="space-y-6">
          {/* Section 1: AI Providers & Telemetry */}
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-white">AI Models & Telemetry Metrics</h3>
              <button
                onClick={loadAdminData}
                className="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 flex items-center gap-1.5 transition-colors"
              >
                <RefreshCw size={12} /> Refresh Metrics
              </button>
            </div>
            
            <div className="grid gap-4">
              {aiProviders.map((p) => {
                const isHealthy = p.status === 'Healthy';
                return (
                  <div key={p.key} className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-4">
                    <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between pb-3 border-b border-slate-900">
                      <div className="space-y-1">
                        <div className="flex items-center gap-3">
                          <span className="font-semibold text-slate-100 text-sm">{p.name}</span>
                          {p.enabled ? (
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${isHealthy ? 'bg-emerald-500/20 text-emerald-300' : p.status === 'Error' ? 'bg-red-500/20 text-red-300' : 'bg-amber-500/20 text-amber-300'}`}>
                              {p.status}
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] font-bold">Disabled</span>
                          )}
                          <span className="text-xs text-slate-500 bg-slate-900 px-2 py-0.5 rounded-full border border-slate-800 font-mono">Priority: {p.priority_index}</span>
                        </div>
                        <div className="text-xs text-slate-500 font-mono">
                          Endpoint: {p.api_url} | Model: {p.model_name}
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center gap-2">
                        <button onClick={() => handleMovePriority(p.key, 'up')} disabled={p.priority_index <= 0} className="p-1.5 bg-slate-900 hover:bg-slate-800 text-slate-400 disabled:opacity-30 rounded border border-slate-800 transition-colors" title="Move Priority Up">
                          <ArrowUp size={14} />
                        </button>
                        <button onClick={() => handleMovePriority(p.key, 'down')} disabled={p.priority_index === -1 || p.priority_index >= aiPriority.length - 1} className="p-1.5 bg-slate-900 hover:bg-slate-800 text-slate-400 disabled:opacity-30 rounded border border-slate-800 transition-colors" title="Move Priority Down">
                          <ArrowDown size={14} />
                        </button>
                        
                        <button onClick={() => handleTestProvider(p.key)} className="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded transition-colors">
                          Test Connection
                        </button>
                        
                        <button onClick={() => handleReloadModels(p.key)} className="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded transition-colors">
                          Reload Models
                        </button>
                        
                        <button 
                          onClick={() => handleToggleProvider(p.key)}
                          className={`px-3 py-1.5 text-xs font-semibold rounded border transition-colors ${p.enabled ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/30' : 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border-emerald-500/30'}`}
                        >
                          {p.enabled ? 'Disable' : 'Enable'}
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs">
                      {/* Telemetry Metrics */}
                      <div className="space-y-1.5 p-3 bg-slate-900/40 rounded border border-slate-900">
                        <div className="font-semibold text-slate-300 flex items-center gap-1.5"><Activity size={14} className="text-violet-400"/> Operational Telemetry</div>
                        <div className="flex justify-between text-slate-400"><span>Avg Latency:</span> <span className="font-mono text-slate-200">{p.latency ? `${p.latency.toFixed(0)}ms` : '--'}</span></div>
                        <div className="flex justify-between text-slate-400"><span>P95 Latency:</span> <span className="font-mono text-slate-200">{p.p95_latency ? `${p.p95_latency.toFixed(0)}ms` : '--'}</span></div>
                        <div className="flex justify-between text-slate-400"><span>Success Rate:</span> <span className="font-mono text-emerald-400 font-bold">{p.success_rate ? `${p.success_rate.toFixed(1)}%` : '100%'}</span></div>
                        <div className="flex justify-between text-slate-400"><span>Requests:</span> <span className="font-mono text-slate-200">{p.requests}</span></div>
                      </div>

                      {/* Exceptions & Retries */}
                      <div className="space-y-1.5 p-3 bg-slate-900/40 rounded border border-slate-900">
                        <div className="font-semibold text-slate-300 flex items-center gap-1.5"><Clock size={14} className="text-violet-400"/> Fallbacks & Failures</div>
                        <div className="flex justify-between text-slate-400"><span>Retry Count:</span> <span className="font-mono text-slate-200">{p.retry_count}</span></div>
                        <div className="flex justify-between text-slate-400"><span>Fallback Count:</span> <span className="font-mono text-slate-200">{p.fallback_count}</span></div>
                        <div className="flex justify-between text-slate-400"><span>Timeout Count:</span> <span className="font-mono text-slate-200">{p.timeout_count}</span></div>
                        <div className="flex justify-between text-slate-400"><span>Uptime Check:</span> <span className="font-mono text-slate-300">{(p.last_health_check) ? new Date(p.last_health_check).toLocaleTimeString() : 'Never'}</span></div>
                      </div>

                      {/* Model Capabilities */}
                      <div className="space-y-1.5 p-3 bg-slate-900/40 rounded border border-slate-900">
                        <div className="font-semibold text-slate-300 flex items-center gap-1.5"><Layers size={14} className="text-violet-400"/> Capabilities</div>
                        <div className="flex justify-between text-slate-400"><span>Context Length:</span> <span className="font-mono text-slate-200">{p.capabilities?.context_length || '4096'} tokens</span></div>
                        <div className="flex justify-between text-slate-400"><span>JSON Extraction:</span> <span className="font-mono">{p.capabilities?.json_mode ? <span className="text-emerald-400">Yes</span> : <span className="text-slate-500">No</span>}</span></div>
                        <div className="flex justify-between text-slate-400"><span>Vision Support:</span> <span className="font-mono">{p.capabilities?.vision ? <span className="text-emerald-400">Yes</span> : <span className="text-slate-500">No</span>}</span></div>
                        <div className="flex justify-between text-slate-400"><span>Streaming:</span> <span className="font-mono">{p.capabilities?.streaming ? <span className="text-emerald-400">Yes</span> : <span className="text-slate-500">No</span>}</span></div>
                      </div>
                    </div>

                    {p.last_error && (
                      <div className="p-2.5 bg-red-500/10 border border-red-500/20 rounded text-[11px] font-mono text-red-400">
                        <strong>Last Error ({new Date(p.last_error.timestamp).toLocaleTimeString()}):</strong> {p.last_error.message}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Section 2: Document Type Routing Rules */}
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-base font-semibold text-white">Document-Type Orchestrator Routing</h3>
            <p className="text-xs text-slate-400">
              Configure the prioritized provider fallback list for each processed document classification.
            </p>
            <div className="grid gap-4">
              {aiRoutingRules.map((rule) => {
                return (
                  <div key={rule.document_type} className="p-4 bg-slate-950 rounded-lg border border-slate-800 flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-200 capitalize text-sm">{rule.document_type.replace('_', ' ')}</div>
                      <div className="text-[11px] text-slate-500 mt-1 flex flex-wrap gap-1">
                        Priority Order: 
                        {rule.provider_keys.length > 0 ? rule.provider_keys.map((k, idx) => (
                          <span key={k} className="px-1.5 py-0.5 bg-slate-900 text-slate-300 rounded font-mono text-[10px] border border-slate-800">
                            {idx + 1}. {k}
                          </span>
                        )) : <span className="text-red-400 italic">None (Will fail execution)</span>}
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-1">
                      {aiProviders.map((p) => {
                        const isSelected = rule.provider_keys.includes(p.key);
                        return (
                          <button
                            key={p.key}
                            onClick={() => {
                              const newKeys = isSelected
                                ? rule.provider_keys.filter((k) => k !== p.key)
                                : [...rule.provider_keys, p.key];
                              handleUpdateRoutingRule(rule.document_type, newKeys);
                            }}
                            className={`px-2.5 py-1 text-xs rounded border transition-colors ${
                              isSelected
                                ? 'bg-violet-600/20 text-violet-300 border-violet-500/30'
                                : 'bg-slate-900 text-slate-500 border-slate-800 hover:text-slate-300'
                            }`}
                          >
                            {p.name}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Tab 6: Ops & Backups */}
      {activeSubTab === 'ops' && (
        <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h3 className="text-base font-semibold text-white">Operations & Backup Control</h3>
              <p className="text-xs text-slate-400 mt-1">Manual system snapshots & RabbitMQ queue management</p>
            </div>
            <button
              onClick={handleTriggerBackup}
              className="px-4 py-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg flex items-center gap-2 transition-colors"
            >
              <HardDrive size={14} /> Trigger System Snapshot Backup
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
