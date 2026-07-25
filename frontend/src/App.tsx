import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useNavigate, Link, useParams } from 'react-router-dom';
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
import { ReviewWorkspace } from './features/reviews/components/ReviewWorkspace';
import { apiClient } from './lib/api-client';

const Header = () => {
  const { logout } = useAuthStore();
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Document Workspace' },
    { path: '/analytics', label: 'Analytics & BI' },
    { path: '/learning', label: 'Continuous Learning' },
    { path: '/admin', label: 'Enterprise Admin' },
    { path: '/health', label: 'System Health' },
    { path: '/audit', label: 'Security Audit Logs' }
  ];

  return (
    <header className="px-6 py-4 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <span className="w-2.5 h-2.5 bg-brand-500 rounded-full animate-pulse"></span>
          HIR Platform <span className="text-xs text-slate-400 font-normal">v1.0 (Core)</span>
        </h1>
        
        <nav className="flex items-center gap-3 ml-4">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
                (item.path === '/' && location.pathname === '/') || (item.path !== '/' && location.pathname.startsWith(item.path))
                  ? 'bg-violet-600 text-white' 
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
      <button
        onClick={logout}
        className="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition-colors"
      >
        Sign Out
      </button>
    </header>
  );
};

const WorkspaceLayout = () => {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [documents, setDocuments] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    const fetchDocs = async () => {
      if (!selectedProjectId) return;
      try {
        const response = await apiClient.get(`/documents/${selectedProjectId}`);
        if (isMounted) {
          setDocuments(response.data);
        }
      } catch (err) {
        console.error('Failed to fetch documents', err);
      }
    };

    fetchDocs();
    const interval = setInterval(fetchDocs, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [selectedProjectId]);

  const handleDeleteDocument = async (docId: string) => {
    try {
      await apiClient.delete(`/documents/${docId}`);
      if (selectedProjectId) {
        const response = await apiClient.get(`/documents/${selectedProjectId}`);
        setDocuments(response.data);
      }
    } catch (err) {
      console.error('Failed to delete document', err);
    }
  };

  const handleProcessDocument = async (docId: string, providerKey?: string) => {
    try {
      await apiClient.post(`/documents/${docId}/process`, {
        ai_provider: providerKey || null
      });
      if (selectedProjectId) {
        const response = await apiClient.get(`/documents/${selectedProjectId}`);
        setDocuments(response.data);
      }
    } catch (err) {
      console.error('Failed to process document', err);
    }
  };

  return (
    <>
      <aside className="w-80 bg-slate-900/50 border-r border-slate-800 p-6 overflow-y-auto">
        <ProjectList
          selectedProjectId={selectedProjectId}
          onSelectProject={(id) => {
            setSelectedProjectId(id);
          }}
        />
      </aside>
      <main className="flex-1 flex flex-col overflow-hidden">
        {selectedProjectId ? (
          <div className="flex-1 p-8 overflow-y-auto space-y-6">
            <div className="grid grid-cols-1 gap-6">
              <DocumentUpload
                projectId={selectedProjectId}
                onUploadSuccess={async () => {
                  const response = await apiClient.get(`/documents/${selectedProjectId}`);
                  setDocuments(response.data);
                }}
              />
              <DocumentList 
                documents={documents} 
                onReviewDocument={(docId) => navigate(`/review/${docId}`)}
                onProcessDocument={handleProcessDocument}
                onDeleteDocument={handleDeleteDocument}
              />
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
            <p className="text-sm italic">Select or create a project to manage documents.</p>
          </div>
        )}
      </main>
    </>
  );
};

const ReviewLayout = () => {
  const navigate = useNavigate();
  const { docId } = useParams<{ docId: string }>();

  if (!docId) return <Navigate to="/" replace />;

  return (
    <main className="flex-1 flex flex-col overflow-hidden">
      <div className="flex flex-col h-full bg-slate-950 overflow-hidden">
        <div className="bg-slate-900 px-6 py-3 border-b border-slate-800 flex items-center justify-between shrink-0">
          <span className="text-xs font-semibold text-slate-300 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-yellow-500 rounded-full"></span>
            Reviewing Document ID: <code className="font-mono text-violet-400">{docId}</code>
          </span>
          <button
            onClick={() => navigate('/')}
            className="px-3 py-1 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded transition-colors"
          >
            ← Back to Queue
          </button>
        </div>
        <div className="flex-1 overflow-hidden">
          <ReviewWorkspace docId={docId} />
        </div>
      </div>
    </main>
  );
};

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuthStore();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      <Header />
      <div className="flex-1 flex overflow-hidden">
        {children}
      </div>
    </div>
  );
};

const App: React.FC = () => {
  const { isAuthenticated } = useAuthStore();

  return (
    <Router>
      <Routes>
        <Route path="/login" element={
          !isAuthenticated ? (
            <div className="min-h-screen bg-slate-950 flex flex-col justify-center">
              <Login />
            </div>
          ) : <Navigate to="/" replace />
        } />
        
        <Route path="/" element={<ProtectedRoute><WorkspaceLayout /></ProtectedRoute>} />
        <Route path="/review/:docId" element={<ProtectedRoute><ReviewLayout /></ProtectedRoute>} />
        
        <Route path="/analytics" element={<ProtectedRoute><main className="flex-1 p-8 overflow-y-auto"><AnalyticsDashboard /></main></ProtectedRoute>} />
        <Route path="/learning" element={<ProtectedRoute><main className="flex-1 p-8 overflow-y-auto"><LearningDashboard /></main></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute><main className="flex-1 p-8 overflow-y-auto"><AdminDashboard /></main></ProtectedRoute>} />
        <Route path="/health" element={<ProtectedRoute><main className="flex-1 p-8 overflow-y-auto"><HealthDashboard /></main></ProtectedRoute>} />
        <Route path="/audit" element={<ProtectedRoute><main className="flex-1 p-8 overflow-y-auto"><AuditDashboard /></main></ProtectedRoute>} />
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
};

export default App;
