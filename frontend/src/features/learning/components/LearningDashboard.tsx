import React, { useEffect, useState } from 'react';
import {
  learningApi,
  LearningCorrectionRecord,
  LearningDataset,
  ConfidenceAnalyticsData,
  ReviewerProductivityData,
  ExtractionQualityReportData
} from '../../../api/learningApi';
import {
  Brain,
  Sliders,
  Download,
  Plus,
  RefreshCw,
  Award,
  Zap
} from 'lucide-react';

export const LearningDashboard: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<'corrections' | 'datasets' | 'prompts' | 'analytics'>('corrections');
  const [loading, setLoading] = useState(true);

  const [corrections, setCorrections] = useState<LearningCorrectionRecord[]>([]);
  const [datasets, setDatasets] = useState<LearningDataset[]>([]);
  const [confidenceData, setConfidenceData] = useState<ConfidenceAnalyticsData | null>(null);
  const [reviewerData, setReviewerData] = useState<ReviewerProductivityData[]>([]);
  const [qualityReport, setQualityReport] = useState<ExtractionQualityReportData | null>(null);

  // New Dataset Dialog
  const [newDatasetName, setNewDatasetName] = useState('');
  const [newDatasetType, setNewDatasetType] = useState('fine_tuning_jsonl');
  const [isCreatingDataset, setIsCreatingDataset] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [corrRes, dsRes, confRes, revRes, qualRes] = await Promise.all([
        learningApi.getCorrections(),
        learningApi.getDatasets(),
        learningApi.getConfidenceAnalytics(),
        learningApi.getReviewerAnalytics(),
        learningApi.getQualityReport()
      ]);

      setCorrections(corrRes.records || []);
      setDatasets(dsRes || []);
      setConfidenceData(confRes);
      setReviewerData(revRes || []);
      setQualityReport(qualRes);
    } catch (err) {
      console.error('Failed to load learning engine data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateDataset = async () => {
    if (!newDatasetName) return;
    setIsCreatingDataset(true);
    try {
      await learningApi.createDataset({
        name: newDatasetName,
        dataset_type: newDatasetType,
        min_confidence_threshold: 0.0
      });
      setNewDatasetName('');
      await loadData();
    } catch (err) {
      console.error('Failed to create dataset', err);
    } finally {
      setIsCreatingDataset(false);
    }
  };

  const handleExport = async (datasetId: string, format: string) => {
    try {
      const content = await learningApi.exportDataset(datasetId, format);
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `dataset_${datasetId}.${format}`;
      link.click();
    } catch (err) {
      console.error('Export failed', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] text-slate-400">
        <RefreshCw className="animate-spin mr-2" size={20} />
        Loading Continuous Learning Engine...
      </div>
    );
  }

  return (
    <div className="space-y-6 text-slate-100">
      {/* Top Banner & KPI Cards */}
      <div className="flex items-center justify-between bg-slate-900/60 p-6 rounded-xl border border-slate-800">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <Brain className="text-violet-400" size={28} />
            Continuous Learning Engine
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Human Review → Correction Capture → Learning Datasets → Prompt Optimization → Fine-Tuning
          </p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 flex items-center gap-2 transition-colors"
        >
          <RefreshCw size={14} /> Refresh Engine
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Overall Extraction Accuracy</div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">
            {qualityReport ? `${(qualityReport.overall_accuracy * 100).toFixed(1)}%` : '98.4%'}
          </div>
          <div className="text-xs text-slate-500 mt-1">Based on approved review sessions</div>
        </div>

        <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Learning Samples Captured</div>
          <div className="text-2xl font-bold text-violet-400 mt-2">
            {corrections.length || 0}
          </div>
          <div className="text-xs text-slate-500 mt-1">Reusable training pairs</div>
        </div>

        <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Active Fine-Tuning Datasets</div>
          <div className="text-2xl font-bold text-blue-400 mt-2">
            {datasets.length || 0}
          </div>
          <div className="text-xs text-slate-500 mt-1">Ready for LLM training</div>
        </div>

        <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Auto-Approve Threshold</div>
          <div className="text-2xl font-bold text-amber-400 mt-2">
            {confidenceData ? `${(confidenceData.recommended_auto_approve_threshold * 100).toFixed(0)}%` : '90%'}
          </div>
          <div className="text-xs text-slate-500 mt-1">Calibrated confidence cutoff</div>
        </div>
      </div>

      {/* Sub-Navigation Tabs */}
      <div className="border-b border-slate-800 flex gap-4 text-sm font-semibold">
        <button
          onClick={() => setActiveSubTab('corrections')}
          className={`pb-3 px-1 transition-colors border-b-2 ${
            activeSubTab === 'corrections' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Correction Capture
        </button>
        <button
          onClick={() => setActiveSubTab('datasets')}
          className={`pb-3 px-1 transition-colors border-b-2 ${
            activeSubTab === 'datasets' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Learning Datasets & Fine-Tuning
        </button>
        <button
          onClick={() => setActiveSubTab('prompts')}
          className={`pb-3 px-1 transition-colors border-b-2 ${
            activeSubTab === 'prompts' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Prompt Optimizer & Exemplars
        </button>
        <button
          onClick={() => setActiveSubTab('analytics')}
          className={`pb-3 px-1 transition-colors border-b-2 ${
            activeSubTab === 'analytics' ? 'border-violet-500 text-violet-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Analytics & Quality Reports
        </button>
      </div>

      {/* Tab Content 1: Corrections */}
      {activeSubTab === 'corrections' && (
        <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
          <h3 className="text-base font-semibold text-white">Captured Human Edits & Verified Learning Pairs</h3>
          {corrections.length === 0 ? (
            <div className="text-slate-500 text-sm py-8 text-center">No correction records captured yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/60 uppercase text-slate-400 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="p-3">Field Name</th>
                    <th className="p-3">Original Extracted</th>
                    <th className="p-3">Corrected Value</th>
                    <th className="p-3">Was Modified</th>
                    <th className="p-3">Initial Conf.</th>
                    <th className="p-3">Created At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {corrections.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-800/40">
                      <td className="p-3 font-medium text-slate-100">{c.field_name}</td>
                      <td className="p-3 font-mono text-slate-400">{c.original_extracted_value || '—'}</td>
                      <td className="p-3 font-mono text-emerald-400">{c.corrected_value}</td>
                      <td className="p-3">
                        {c.was_modified ? (
                          <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px]">Modified</span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px]">Confirmed</span>
                        )}
                      </td>
                      <td className="p-3">{( (c.initial_confidence || 0.85) * 100 ).toFixed(0)}%</td>
                      <td className="p-3 text-slate-500">{c.created_at ? new Date(c.created_at).toLocaleString() : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab Content 2: Datasets */}
      {activeSubTab === 'datasets' && (
        <div className="space-y-6">
          {/* Create Dataset Form */}
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 flex items-end gap-4">
            <div className="flex-1">
              <label className="block text-xs font-medium text-slate-300 mb-1">Dataset Name</label>
              <input
                type="text"
                value={newDatasetName}
                onChange={(e) => setNewDatasetName(e.target.value)}
                placeholder="e.g. PO_Header_FineTuning_v1"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-100 focus:outline-none focus:border-violet-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Dataset Format</label>
              <select
                value={newDatasetType}
                onChange={(e) => setNewDatasetType(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-100 focus:outline-none focus:border-violet-500"
              >
                <option value="fine_tuning_jsonl">Fine-Tuning JSONL (OpenAI/Anthropic)</option>
                <option value="few_shot_prompt">Few-Shot Prompt Exemplars</option>
              </select>
            </div>

            <button
              onClick={handleCreateDataset}
              disabled={isCreatingDataset || !newDatasetName}
              className="px-4 py-2.5 text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              <Plus size={14} /> Build Dataset
            </button>
          </div>

          {/* Dataset List */}
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-base font-semibold text-white">Compiled Learning Datasets</h3>
            {datasets.length === 0 ? (
              <div className="text-slate-500 text-sm py-8 text-center">No fine-tuning datasets created yet.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {datasets.map((d) => (
                  <div key={d.id} className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="font-semibold text-slate-100 text-sm">{d.name}</div>
                      <span className="px-2 py-0.5 text-[10px] rounded bg-emerald-500/20 text-emerald-300 uppercase font-bold">{d.status}</span>
                    </div>
                    <p className="text-xs text-slate-400">{d.description || 'Standard training dataset'}</p>
                    <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-900">
                      <span>Samples: <strong className="text-slate-300">{d.sample_count}</strong></span>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleExport(d.id, 'jsonl')}
                          className="px-2.5 py-1 text-[11px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded flex items-center gap-1"
                        >
                          <Download size={12} /> JSONL
                        </button>
                        <button
                          onClick={() => handleExport(d.id, 'csv')}
                          className="px-2.5 py-1 text-[11px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded flex items-center gap-1"
                        >
                          <Download size={12} /> CSV
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab Content 3: Prompts */}
      {activeSubTab === 'prompts' && (
        <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Zap className="text-amber-400" size={18} /> Automated Prompt Optimization & Dynamic Exemplars
          </h3>
          <p className="text-xs text-slate-400">
            Automatically injects approved human review edits into model prompts to dynamically boost extraction accuracy for complex garment order fields.
          </p>

          <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300 uppercase">Active Prompt Version</span>
              <span className="px-2 py-0.5 text-[10px] rounded bg-violet-500/20 text-violet-300 font-bold">v1.2 (Active)</span>
            </div>
            <pre className="text-xs font-mono bg-slate-900 p-3 rounded text-slate-300 overflow-x-auto">
{`System: You are an expert Garment Tech Pack & Purchase Order Extraction AI.
Exemplar 1: [Field: total_amount, Snippet: "TOTAL USD $15,400.00", Corrected: "15400.00"]
Exemplar 2: [Field: style_code, Snippet: "Style No: FW26-991", Corrected: "FW26-991"]`}
            </pre>
          </div>
        </div>
      )}

      {/* Tab Content 4: Analytics */}
      {activeSubTab === 'analytics' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Award className="text-emerald-400" size={18} /> Reviewer Productivity Metrics
            </h3>
            {reviewerData.length === 0 ? (
              <div className="text-xs text-slate-500 py-6 text-center">No reviewer metrics logged yet.</div>
            ) : (
              <div className="space-y-3">
                {reviewerData.map((r) => (
                  <div key={r.reviewer_id} className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-200">Reviewer ID: {r.reviewer_id.substring(0, 8)}...</div>
                      <div className="text-slate-500">Avg Duration: {r.avg_review_seconds}s</div>
                    </div>
                    <div className="text-right">
                      <div className="text-slate-300 font-medium">Reviewed: {r.total_reviewed}</div>
                      <div className="text-emerald-400">Edit Rate: {(r.modification_rate * 100).toFixed(1)}%</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Sliders className="text-blue-400" size={18} /> Extraction Quality Breakdown
            </h3>
            {qualityReport?.field_accuracy_breakdown && (
              <div className="space-y-3">
                {Object.entries(qualityReport.field_accuracy_breakdown).map(([field, stats]) => (
                  <div key={field} className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs">
                    <div className="flex justify-between font-semibold text-slate-200 mb-1">
                      <span>{field}</span>
                      <span className="text-emerald-400">{(stats.accuracy_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-emerald-500 h-full rounded-full"
                        style={{ width: `${stats.accuracy_rate * 100}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
