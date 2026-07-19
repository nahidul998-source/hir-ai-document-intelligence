import React, { useState, useEffect } from 'react';
import { useAuthStore } from './stores/authStore';
import { Login } from './features/auth/components/Login';
import { ProjectList } from './features/projects/components/ProjectList';
import { DocumentUpload } from './features/documents/components/DocumentUpload';
import { DocumentList } from './features/documents/components/DocumentList';
import { HealthDashboard } from './features/monitoring/components/HealthDashboard';
import { AuditDashboard } from './features/monitoring/components/AuditDashboard';
import { LearningDashboard } from './features/learning/components/LearningDashboard';
import { AdminDashboard } from './features/admin/components/AdminDashboard';
import { AnalyticsDashboard } from './features/analytics/components/AnalyticsDashboard';
import { apiClient } from './lib/api-client';

const App: React.FC = () => {
  const { isAuthenticated, logout } = useAuthStore();
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [documents, setDocuments] = useState([]);
  const [currentTab, setCurrentTab] = useState<'workspace' | 'health' | 'audit' | 'learning' | 'admin' | 'analytics'>('workspace');

  const fetchDocuments = async () => {
    if (!selectedProjectId) return;
    try {
      const response = await apiClient.get(`/documents/${selectedProjectId}`);
      setDocuments(response.data);
    } catch (err) {
      console.error('Failed to fetch documents', err);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [selectedProjectId]);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col justify-center">
        <Login />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Top Header */}
      <header className="px-6 py-4 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-brand-500 rounded-full animate-pulse"></span>
            HIR Platform <span className="text-xs text-slate-400 font-normal">v1.0 (Core)</span>
          </h1>
          
          <nav className="flex items-center gap-3 ml-4">
            <button
              onClick={() => setCurrentTab('workspace')}
              className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
                currentTab === 'workspace' ? 'bg-violet-600 text-white' : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
              }`}
            >
              Document Workspace
            </button>
            <button
              onClick={() => setCurrentTab('analytics')}
              className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
                currentTab === 'analytics' ? 'bg-violet-600 text-white' : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
              }`}
            >
              Analytics & BI
            </button>
            <button
              onClick={() => setCurrentTab('learning')}
              className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
                currentTab === 'learning' ? 'bg-violet-600 text-white' : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
              }`}
            >
              Continuous Learning
            </button>
            <button
              onClick={() => setCurrentTab('admin')}
              className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
                currentTab === 'admin' ? 'bg-violet-600 text-white' : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
              }`}
            >
              Enterprise Admin
            </button>
            <button
              onClick={() => setCurrentTab('health')}
              className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
                currentTab === 'health' ? 'bg-violet-600 text-white' : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
              }`}
            >
              System Health
            </button>
            <button
              onClick={() => setCurrentTab('audit')}
              className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
                currentTab === 'audit' ? 'bg-violet-600 text-white' : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
              }`}
            >
              Security Audit Logs
            </button>
          </nav>
        </div>
        <button
          onClick={logout}
          className="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition-colors"
        >
          Sign Out
        </button>
      </header>

      {/* Main Workspace */}
      <div className="flex-1 flex overflow-hidden">
        {currentTab === 'workspace' ? (
          <>
            {/* Sidebar */}
            <aside className="w-80 bg-slate-900/50 border-r border-slate-800 p-6 overflow-y-auto">
              <ProjectList
                selectedProjectId={selectedProjectId}
                onSelectProject={setSelectedProjectId}
              />
            </aside>

            {/* Dashboard Area */}
            <main className="flex-1 p-8 overflow-y-auto space-y-6">
              {selectedProjectId ? (
                <>
                  <div className="grid grid-cols-1 gap-6">
                    <DocumentUpload
                      projectId={selectedProjectId}
                      onUploadSuccess={fetchDocuments}
                    />
                    <DocumentList documents={documents} />
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center min-h-[50vh] text-slate-500">
                  <p className="text-sm italic">Select or create a project to manage documents.</p>
                </div>
              )}
            </main>
          </>
        ) : (
          <main className="flex-1 p-8 overflow-y-auto">
            {currentTab === 'analytics' ? (
              <AnalyticsDashboard />
            ) : currentTab === 'learning' ? (
              <LearningDashboard />
            ) : currentTab === 'admin' ? (
              <AdminDashboard />
            ) : currentTab === 'health' ? (
              <HealthDashboard />
            ) : (
              <AuditDashboard />
            )}
          </main>
        )}
      </div>
    </div>
  );
};

export default App;

