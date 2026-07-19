import React, { useEffect, useState } from 'react';
import {
  adminApi,
  AdminUser,
  Tenant,
  FeatureFlag,
  SystemConfig,
  ApiKeyData
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
  Cpu
} from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<'users' | 'tenants' | 'flags' | 'keys' | 'ops'>('users');
  const [loading, setLoading] = useState(true);

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [configs, setConfigs] = useState<SystemConfig[]>([]);
  const [apiKeys, setApiKeys] = useState<ApiKeyData[]>([]);

  // New Tenant Modal State
  const [tenantName, setTenantName] = useState('');
  const [tenantCode, setTenantCode] = useState('');

  // New Api Key Modal State
  const [keyName, setKeyName] = useState('');
  const [createdRawKey, setCreatedRawKey] = useState<string | null>(null);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [uRes, tRes, fRes, cfgRes, kRes] = await Promise.all([
        adminApi.getUsers(),
        adminApi.getTenants(),
        adminApi.getFeatureFlags(),
        adminApi.getSystemConfigs(),
        adminApi.getApiKeys()
      ]);

      setUsers(uRes || []);
      setTenants(tRes || []);
      setFlags(fRes || []);
      setConfigs(cfgRes || []);
      setApiKeys(kRes || []);
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

      {/* Tab 5: Ops & Backups */}
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
