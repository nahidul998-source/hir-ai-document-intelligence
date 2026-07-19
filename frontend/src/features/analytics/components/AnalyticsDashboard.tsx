import React, { useEffect, useState } from 'react';
import {
  analyticsApi,
  OverviewMetrics,
  AccuracyAnalytics,
  TokenCostMetrics,
  ReviewerProductivity,
  CommercialAnalytics
} from '../../../api/analyticsApi';
import {
  BarChart3,
  TrendingUp,
  FileCheck,
  Zap,
  DollarSign,
  Building2,
  Download,
  CheckCircle2,
  RefreshCw,
  Cpu,
  Award,
  Users
} from 'lucide-react';

export const AnalyticsDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);

  const [overview, setOverview] = useState<OverviewMetrics | null>(null);
  const [accuracy, setAccuracy] = useState<AccuracyAnalytics | null>(null);
  const [tokens, setTokens] = useState<TokenCostMetrics | null>(null);
  const [productivity, setProductivity] = useState<ReviewerProductivity | null>(null);
  const [commercial, setCommercial] = useState<CommercialAnalytics | null>(null);
  const [distribution, setDistribution] = useState<Record<string, number>>({});

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const [ovRes, accRes, tokRes, prodRes, commRes, distRes] = await Promise.all([
        analyticsApi.getOverview(),
        analyticsApi.getAccuracy(),
        analyticsApi.getTokenUsage(),
        analyticsApi.getReviewerProductivity(),
        analyticsApi.getBuyerFactory(),
        analyticsApi.getConfidenceDistribution()
      ]);

      setOverview(ovRes);
      setAccuracy(accRes);
      setTokens(tokRes);
      setProductivity(prodRes);
      setCommercial(commRes);
      setDistribution(distRes);
    } catch (err) {
      console.error('Failed to load BI analytics data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] text-slate-400">
        <RefreshCw className="animate-spin mr-2" size={20} />
        Loading Executive Analytics & BI Engine...
      </div>
    );
  }

  return (
    <div className="space-y-6 text-slate-100">
      {/* Top Banner */}
      <div className="flex items-center justify-between bg-slate-900/60 p-6 rounded-xl border border-slate-800">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <BarChart3 className="text-violet-400" size={28} />
            Executive Analytics & Business Intelligence
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Real-time Telemetry, AI Extraction Accuracy, Cost Estimation, Commercial Buyer/Factory Volume & Export Engine
          </p>
        </div>

        {/* Export Center Controls */}
        <div className="flex items-center gap-2">
          <a
            href={analyticsApi.exportReport('csv')}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <Download size={14} /> Export CSV
          </a>
          <a
            href={analyticsApi.exportReport('excel')}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-2 text-xs font-semibold bg-emerald-700/80 hover:bg-emerald-600 text-white rounded-lg border border-emerald-600 flex items-center gap-1.5 transition-colors"
          >
            <Download size={14} /> Export Excel
          </a>
          <a
            href={analyticsApi.exportReport('pdf')}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-2 text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white rounded-lg flex items-center gap-1.5 transition-colors"
          >
            <Download size={14} /> Printable PDF
          </a>
        </div>
      </div>

      {/* KPI Cards Row */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/50 p-5 rounded-xl border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
              <span>Documents Processed</span>
              <FileCheck className="text-violet-400" size={18} />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">{overview.total_documents}</div>
            <div className="text-[11px] text-slate-500 flex justify-between pt-1 border-t border-slate-800/60">
              <span>Completed: <strong className="text-emerald-400">{overview.completed_documents}</strong></span>
              <span>Pending: <strong className="text-amber-400">{overview.review_pending_documents}</strong></span>
            </div>
          </div>

          <div className="bg-slate-900/50 p-5 rounded-xl border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
              <span>AI Accuracy</span>
              <TrendingUp className="text-emerald-400" size={18} />
            </div>
            <div className="text-2xl font-bold text-emerald-400 tracking-tight">{overview.ai_accuracy_pct}%</div>
            <div className="text-[11px] text-slate-500 pt-1 border-t border-slate-800/60">
              ERP Success: <strong className="text-slate-200">{overview.erp_success_rate_pct}%</strong>
            </div>
          </div>

          <div className="bg-slate-900/50 p-5 rounded-xl border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
              <span>Estimated AI Cost</span>
              <DollarSign className="text-emerald-400" size={18} />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">${overview.estimated_ai_cost_usd} USD</div>
            <div className="text-[11px] text-slate-500 pt-1 border-t border-slate-800/60">
              Tokens: <strong className="text-slate-200">{(overview.total_tokens_consumed / 1000000).toFixed(2)}M</strong>
            </div>
          </div>

          <div className="bg-slate-900/50 p-5 rounded-xl border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
              <span>SLA Compliance</span>
              <CheckCircle2 className="text-violet-400" size={18} />
            </div>
            <div className="text-2xl font-bold text-violet-400 tracking-tight">{overview.sla_compliance_pct}%</div>
            <div className="text-[11px] text-slate-500 pt-1 border-t border-slate-800/60">
              Target Threshold: <strong className="text-slate-200">95.0%</strong>
            </div>
          </div>
        </div>
      )}

      {/* Row 2: Field Accuracy & Confidence Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {accuracy && (
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Award className="text-emerald-400" size={18} /> Field-Level AI Extraction Accuracy
            </h3>
            <div className="space-y-3 text-xs">
              {Object.entries(accuracy.field_accuracy).map(([field, score]) => (
                <div key={field} className="space-y-1">
                  <div className="flex justify-between text-slate-300 font-medium">
                    <span className="capitalize">{field.replace('_', ' ')}</span>
                    <span className="text-emerald-400 font-semibold">{score}%</span>
                  </div>
                  <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${score}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Zap className="text-amber-400" size={18} /> Model Confidence Distribution Histogram
          </h3>
          <div className="space-y-3 text-xs">
            {Object.entries(distribution).map(([bin, count]) => (
              <div key={bin} className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
                <span className="font-semibold text-slate-200">Range {bin}</span>
                <span className="px-2.5 py-1 rounded bg-violet-500/20 text-violet-300 font-mono text-xs">{count} samples</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 3: Token Usage Cost & Reviewer Productivity */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {tokens && (
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Cpu className="text-violet-400" size={18} /> AI Model Provider Token & Cost Breakdown
            </h3>
            <div className="space-y-3 text-xs">
              {tokens.providers.map((p) => (
                <div key={p.model} className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-slate-200">{p.provider} ({p.model})</div>
                    <div className="text-slate-500">{(p.tokens / 1000).toFixed(0)}k tokens</div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-emerald-400">${p.cost_usd} USD</div>
                    <div className="text-slate-500">{p.share_pct}% usage share</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {productivity && (
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Users className="text-violet-400" size={18} /> Reviewer Productivity & Performance
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <div className="text-slate-400">Avg Review Time</div>
                <div className="text-lg font-bold text-white mt-1">{productivity.avg_review_time_seconds} sec</div>
              </div>
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <div className="text-slate-400">Field Correction Rate</div>
                <div className="text-lg font-bold text-emerald-400 mt-1">{productivity.field_correction_rate_pct}%</div>
              </div>
            </div>

            <div className="space-y-2 text-xs pt-2">
              <div className="font-semibold text-slate-300">Top Performing Reviewers</div>
              {productivity.top_reviewers.map((r) => (
                <div key={r.reviewer_name} className="p-2.5 bg-slate-950 rounded border border-slate-800 flex justify-between text-slate-300">
                  <span>{r.reviewer_name}</span>
                  <span className="text-violet-400 font-mono">{r.reviews_count} reviews ({r.avg_time_sec}s avg)</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Row 4: Commercial Buyer & Factory Analytics */}
      {commercial && (
        <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Building2 className="text-violet-400" size={18} /> Buyer & Factory Commercial Volume
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Buyer Table */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-slate-400 uppercase">Top Garment Buyers</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-800/60 uppercase text-slate-400 font-semibold border-b border-slate-700">
                    <tr>
                      <th className="p-2">Buyer</th>
                      <th className="p-2">Volume</th>
                      <th className="p-2">Accuracy</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {commercial.buyers.map((b) => (
                      <tr key={b.buyer_code} className="hover:bg-slate-800/40">
                        <td className="p-2 font-medium text-slate-100">{b.buyer_name}</td>
                        <td className="p-2 font-mono text-slate-300">{b.volume} docs</td>
                        <td className="p-2 text-emerald-400 font-semibold">{b.accuracy_pct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Factory Table */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-slate-400 uppercase">Manufacturing Factory Facilities</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-800/60 uppercase text-slate-400 font-semibold border-b border-slate-700">
                    <tr>
                      <th className="p-2">Factory</th>
                      <th className="p-2">Volume</th>
                      <th className="p-2">Accuracy</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {commercial.factories.map((f) => (
                      <tr key={f.factory_code} className="hover:bg-slate-800/40">
                        <td className="p-2 font-medium text-slate-100">{f.factory_name}</td>
                        <td className="p-2 font-mono text-slate-300">{f.volume} docs</td>
                        <td className="p-2 text-emerald-400 font-semibold">{f.accuracy_pct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
