import React, { useState, useEffect } from 'react';
import { apiClient } from '../../../lib/api-client';
import { 
  Activity, Database, Layers, Cpu, Server, CheckCircle2, 
  AlertTriangle, XCircle, RefreshCw, Clock, ArrowDownUp 
} from 'lucide-react';

interface HealthData {
  status: string;
  timestamp: string;
  services: {
    postgresql: { status: string; latency_ms: number; error?: string };
    redis: { status: string; latency_ms: number; error?: string };
    rabbitmq: { status: string; latency_ms: number; error?: string };
    minio: { status: string; latency_ms: number; error?: string };
    ai_providers: {
      status: string;
      providers: Record<string, { status: string }>;
    };
    workers: {
      ai_worker: { status: string; last_heartbeat: string | null; error?: string };
      erp_worker: { status: string; last_heartbeat: string | null; error?: string };
    };
  };
}

interface QueueStats {
  [key: string]: {
    message_count: number;
    consumer_count: number;
    status: string;
    error?: string;
  };
}

interface JobStats {
  summary: {
    queued: number;
    processing: number;
    completed: number;
    failed: number;
  };
  recent_jobs: Array<{
    id: string;
    document_id: string;
    job_type: string;
    status: string;
    error_message: string | null;
    created_at: string;
    completed_at: string | null;
  }>;
}

export const HealthDashboard: React.FC = () => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [queues, setQueues] = useState<QueueStats | null>(null);
  const [jobs, setJobs] = useState<JobStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(10); // seconds

  const fetchData = async () => {
    setLoading(true);
    try {
      const [healthRes, queuesRes, jobsRes] = await Promise.all([
        apiClient.get('/monitoring/health'),
        apiClient.get('/monitoring/queues'),
        apiClient.get('/monitoring/jobs'),
      ]);
      setHealth(healthRes.data);
      setQueues(queuesRes.data);
      setJobs(jobsRes.data);
    } catch (err) {
      console.error('Observability dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
        return <CheckCircle2 className="w-5 h-5 text-emerald-500" />;
      case 'degraded':
        return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      default:
        return <XCircle className="w-5 h-5 text-rose-500" />;
    }
  };

  const getStatusBgClass = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
        return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400';
      case 'degraded':
        return 'bg-amber-500/10 border-amber-500/20 text-amber-400';
      default:
        return 'bg-rose-500/10 border-rose-500/20 text-rose-400';
    }
  };

  const getServiceStatusIndicator = (status: string) => {
    if (status?.toLowerCase() === 'healthy') {
      return (
        <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold bg-emerald-950/40 border border-emerald-900/30 px-2 py-0.5 rounded-full">
          <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping"></span>
          Online
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1.5 text-xs text-rose-400 font-semibold bg-rose-950/40 border border-rose-900/30 px-2 py-0.5 rounded-full">
        Offline
      </span>
    );
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Controls */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Activity className="w-6 h-6 text-violet-500" />
            Operations & Health Dashboard
          </h2>
          <p className="text-slate-400 text-sm mt-1">Real-time status tracking for HIR microservices, databases, queues, and AI providers.</p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Interval:</span>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="bg-slate-900 text-slate-300 text-xs border border-slate-800 rounded px-2 py-1.5 focus:outline-none focus:border-violet-500"
            >
              <option value={5}>5s</option>
              <option value={10}>10s</option>
              <option value={30}>30s</option>
            </select>
          </div>
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-1.5 text-xs bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-slate-300 border border-slate-800 px-3 py-1.5 rounded transition-all font-semibold"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh Now
          </button>
        </div>
      </div>

      {health && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Overall Health Status Card */}
          <div className={`col-span-1 lg:col-span-4 border rounded-xl p-5 flex items-center justify-between shadow-2xl ${getStatusBgClass(health.status)}`}>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
                {getStatusIcon(health.status)}
              </div>
              <div>
                <h3 className="text-lg font-bold capitalize">System {health.status}</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Last checked: {new Date(health.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
            <div className="text-xs text-slate-500 font-mono">
              HIR-NODE: master-primary-worker-01
            </div>
          </div>

          {/* Infrastructure Health Grid */}
          <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* PostgreSQL */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-5 hover:border-slate-700/60 transition-all flex flex-col justify-between">
              <div className="flex justify-between items-start">
                <div className="flex gap-3 items-center">
                  <div className="p-2.5 bg-slate-800/50 rounded-lg text-indigo-400 border border-slate-800">
                    <Database className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-200">PostgreSQL Database</h4>
                    <p className="text-xs text-slate-500">Active connection pool (max 20)</p>
                  </div>
                </div>
                {getServiceStatusIndicator(health.services.postgresql.status)}
              </div>
              <div className="mt-4 pt-4 border-t border-slate-800/50 flex justify-between items-center text-xs">
                <span className="text-slate-500">Response Latency:</span>
                <span className="font-semibold text-slate-300 font-mono">
                  {health.services.postgresql.status === 'healthy' ? `${health.services.postgresql.latency_ms} ms` : 'N/A'}
                </span>
              </div>
            </div>

            {/* Redis Cache */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-5 hover:border-slate-700/60 transition-all flex flex-col justify-between">
              <div className="flex justify-between items-start">
                <div className="flex gap-3 items-center">
                  <div className="p-2.5 bg-slate-800/50 rounded-lg text-emerald-400 border border-slate-800">
                    <Layers className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-200">Redis Memory Store</h4>
                    <p className="text-xs text-slate-500">Distributed caching & worker tracking</p>
                  </div>
                </div>
                {getServiceStatusIndicator(health.services.redis.status)}
              </div>
              <div className="mt-4 pt-4 border-t border-slate-800/50 flex justify-between items-center text-xs">
                <span className="text-slate-500">Ping Time:</span>
                <span className="font-semibold text-slate-300 font-mono">
                  {health.services.redis.status === 'healthy' ? `${health.services.redis.latency_ms} ms` : 'N/A'}
                </span>
              </div>
            </div>

            {/* RabbitMQ Message Broker */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-5 hover:border-slate-700/60 transition-all flex flex-col justify-between">
              <div className="flex justify-between items-start">
                <div className="flex gap-3 items-center">
                  <div className="p-2.5 bg-slate-800/50 rounded-lg text-amber-400 border border-slate-800">
                    <ArrowDownUp className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-200">RabbitMQ Event Broker</h4>
                    <p className="text-xs text-slate-500">Event-driven topology exchange</p>
                  </div>
                </div>
                {getServiceStatusIndicator(health.services.rabbitmq.status)}
              </div>
              <div className="mt-4 pt-4 border-t border-slate-800/50 flex justify-between items-center text-xs">
                <span className="text-slate-500">Handshake latency:</span>
                <span className="font-semibold text-slate-300 font-mono">
                  {health.services.rabbitmq.status === 'healthy' ? `${health.services.rabbitmq.latency_ms} ms` : 'N/A'}
                </span>
              </div>
            </div>

            {/* MinIO Storage */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-5 hover:border-slate-700/60 transition-all flex flex-col justify-between">
              <div className="flex justify-between items-start">
                <div className="flex gap-3 items-center">
                  <div className="p-2.5 bg-slate-800/50 rounded-lg text-cyan-400 border border-slate-800">
                    <Server className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-200">MinIO Storage Adapter</h4>
                    <p className="text-xs text-slate-500">Raw documents & storage buckets</p>
                  </div>
                </div>
                {getServiceStatusIndicator(health.services.minio.status)}
              </div>
              <div className="mt-4 pt-4 border-t border-slate-800/50 flex justify-between items-center text-xs">
                <span className="text-slate-500">Bucket ping:</span>
                <span className="font-semibold text-slate-300 font-mono">
                  {health.services.minio.status === 'healthy' ? `${health.services.minio.latency_ms} ms` : 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* AI Providers Fallback Health */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-5 hover:border-slate-700/60 transition-all flex flex-col justify-between">
            <div>
              <h4 className="font-bold text-slate-200">AI Provider Engines</h4>
              <p className="text-xs text-slate-500 mb-4">Fallback priority routing</p>
              
              <div className="space-y-3">
                {Object.entries(health.services.ai_providers.providers).map(([name, prov], idx) => (
                  <div key={name} className="flex items-center justify-between p-2.5 bg-slate-950/50 rounded border border-slate-800/60">
                    <span className="text-xs text-slate-300 font-semibold font-mono flex items-center gap-1.5">
                      <span className="text-slate-500">{idx + 1}.</span> {name}
                    </span>
                    <span className={`w-2 h-2 rounded-full ${prov.status === 'healthy' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]' : 'bg-rose-500'}`}></span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="mt-6 pt-4 border-t border-slate-800/50 text-center">
              <span className="text-[10px] text-slate-500 font-semibold">PROVIDER SHIELD ACTIVE</span>
            </div>
          </div>

          {/* Worker Status Indicators */}
          <div className="col-span-1 lg:col-span-4 bg-slate-900/30 border border-slate-800 rounded-xl p-6">
            <h3 className="text-sm font-bold text-slate-200 tracking-wider uppercase mb-4 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-violet-400" />
              Microservice Worker Heartbeats
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* AI Worker */}
              <div className="p-4 bg-slate-950/40 border border-slate-800/50 rounded-lg flex items-center justify-between">
                <div>
                  <div className="text-sm font-bold text-slate-300">AI Processing Worker</div>
                  <div className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    Last heartbeat:{' '}
                    {health.services.workers.ai_worker.last_heartbeat
                      ? new Date(health.services.workers.ai_worker.last_heartbeat).toLocaleTimeString()
                      : 'Never'}
                  </div>
                </div>
                {getServiceStatusIndicator(health.services.workers.ai_worker.status)}
              </div>

              {/* ERP Worker */}
              <div className="p-4 bg-slate-950/40 border border-slate-800/50 rounded-lg flex items-center justify-between">
                <div>
                  <div className="text-sm font-bold text-slate-300">ERP Sync Worker</div>
                  <div className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    Last heartbeat:{' '}
                    {health.services.workers.erp_worker.last_heartbeat
                      ? new Date(health.services.workers.erp_worker.last_heartbeat).toLocaleTimeString()
                      : 'Never'}
                  </div>
                </div>
                {getServiceStatusIndicator(health.services.workers.erp_worker.status)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Queue Monitoring & Job Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Queue Status Table */}
        <div className="col-span-1 lg:col-span-2 bg-slate-900/30 border border-slate-800 rounded-xl p-6">
          <h3 className="text-sm font-bold text-slate-200 tracking-wider uppercase mb-4 flex items-center gap-2">
            <ArrowDownUp className="w-4 h-4 text-violet-400" />
            Queue Lengths & Load Monitoring
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase">
                  <th className="py-2.5">Queue Name</th>
                  <th className="py-2.5">Queued Messages</th>
                  <th className="py-2.5">Active Consumers</th>
                  <th className="py-2.5 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850">
                {queues && Object.entries(queues).map(([name, q]) => (
                  <tr key={name} className="hover:bg-slate-900/20 text-slate-300">
                    <td className="py-3 font-semibold font-mono text-slate-200">{name}</td>
                    <td className="py-3 font-semibold font-mono text-slate-400">{q.message_count}</td>
                    <td className="py-3 font-mono text-slate-400">{q.consumer_count}</td>
                    <td className="py-3 text-right">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        q.status === 'active' ? 'bg-emerald-950 border border-emerald-900 text-emerald-400' :
                        q.status === 'idle' ? 'bg-amber-950 border border-amber-900 text-amber-400' :
                        'bg-slate-900 border border-slate-800 text-slate-400'
                      }`}>
                        {q.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Job statistics Card */}
        {jobs && (
          <div className="bg-slate-900/30 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-200 tracking-wider uppercase mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4 text-violet-400" />
                Pipeline Job Metrics
              </h3>
              
              <div className="grid grid-cols-2 gap-4 mt-2">
                <div className="p-4 bg-slate-950/50 border border-slate-800/80 rounded-lg">
                  <div className="text-xs text-slate-500 font-semibold uppercase">Processing</div>
                  <div className="text-2xl font-bold font-mono text-slate-200 mt-1">{jobs.summary.processing}</div>
                </div>
                <div className="p-4 bg-slate-950/50 border border-slate-800/80 rounded-lg">
                  <div className="text-xs text-slate-500 font-semibold uppercase">Queued</div>
                  <div className="text-2xl font-bold font-mono text-slate-200 mt-1">{jobs.summary.queued}</div>
                </div>
                <div className="p-4 bg-slate-950/50 border border-slate-800/80 rounded-lg">
                  <div className="text-xs text-slate-500 font-semibold uppercase">Completed</div>
                  <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">{jobs.summary.completed}</div>
                </div>
                <div className="p-4 bg-slate-950/50 border border-slate-800/80 rounded-lg">
                  <div className="text-xs text-slate-500 font-semibold uppercase">Failed</div>
                  <div className="text-2xl font-bold font-mono text-rose-400 mt-1">{jobs.summary.failed}</div>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800/60 text-xs text-slate-500 flex justify-between">
              <span>Failed Rate:</span>
              <span className="font-mono font-bold text-slate-400">
                {jobs.summary.completed + jobs.summary.failed > 0 
                  ? `${((jobs.summary.failed / (jobs.summary.completed + jobs.summary.failed)) * 100).toFixed(1)}%`
                  : '0.0%'}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Recent Jobs Table */}
      {jobs && jobs.recent_jobs.length > 0 && (
        <div className="bg-slate-900/30 border border-slate-800 rounded-xl p-6">
          <h3 className="text-sm font-bold text-slate-200 tracking-wider uppercase mb-4">
            Recent Pipeline Jobs
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase">
                  <th className="py-2.5">Job ID</th>
                  <th className="py-2.5">Type</th>
                  <th className="py-2.5">Status</th>
                  <th className="py-2.5">Created At</th>
                  <th className="py-2.5">Completed At</th>
                  <th className="py-2.5 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850">
                {jobs.recent_jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-900/20 text-slate-300">
                    <td className="py-3 font-mono text-slate-200">{job.id.substring(0, 8)}...</td>
                    <td className="py-3 capitalize text-slate-400">{job.job_type}</td>
                    <td className="py-3">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        job.status === 'completed' ? 'bg-emerald-950/40 text-emerald-400' :
                        job.status === 'failed' ? 'bg-rose-950/40 text-rose-400' :
                        'bg-slate-900 text-slate-400'
                      }`}>
                        {job.status}
                      </span>
                    </td>
                    <td className="py-3 text-slate-500">{new Date(job.created_at).toLocaleString()}</td>
                    <td className="py-3 text-slate-500">{job.completed_at ? new Date(job.completed_at).toLocaleString() : 'N/A'}</td>
                    <td className="py-3 text-right max-w-xs truncate text-rose-400/90 font-mono" title={job.error_message || ''}>
                      {job.error_message || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
