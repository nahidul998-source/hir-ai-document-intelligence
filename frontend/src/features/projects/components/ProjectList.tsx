import React, { useState, useEffect } from 'react';
import { apiClient } from '../../../lib/api-client';

interface Project {
  id: string;
  name: string;
  description: string;
  created_at: string;
}

interface ProjectListProps {
  onSelectProject: (projectId: string) => void;
  selectedProjectId: string | null;
}

export const ProjectList: React.FC<ProjectListProps> = ({ onSelectProject, selectedProjectId }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const fetchProjects = async () => {
    try {
      const response = await apiClient.get('/projects/');
      setProjects(response.data);
      if (response.data.length > 0 && !selectedProjectId) {
        onSelectProject(response.data[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch projects', err);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      const response = await apiClient.post('/projects/', { name, description });
      setProjects([...projects, response.data]);
      onSelectProject(response.data.id);
      setName('');
      setDescription('');
      setIsCreating(false);
    } catch (err) {
      console.error('Failed to create project', err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-slate-100">Projects</h3>
        <button
          onClick={() => setIsCreating(!isCreating)}
          className="px-3 py-1.5 text-xs font-semibold bg-brand-600 hover:bg-brand-500 rounded text-slate-100 transition-colors"
        >
          {isCreating ? 'Cancel' : 'New Project'}
        </button>
      </div>

      {isCreating && (
        <form onSubmit={handleCreate} className="p-4 bg-slate-900 border border-slate-800 rounded-lg space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Project Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-sm text-slate-200 focus:outline-none"
              placeholder="e.g. Autumn Techpacks"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-sm text-slate-200 focus:outline-none"
              placeholder="Optional description"
              rows={2}
            />
          </div>
          <button
            type="submit"
            className="w-full py-2 text-xs font-semibold bg-brand-500 hover:bg-brand-400 rounded text-slate-100"
          >
            Create Project
          </button>
        </form>
      )}

      <div className="space-y-2">
        {projects.length === 0 ? (
          <p className="text-slate-500 text-sm italic">No projects found. Create one to begin.</p>
        ) : (
          projects.map((project) => (
            <div
              key={project.id}
              onClick={() => onSelectProject(project.id)}
              className={`p-3 rounded-lg border cursor-pointer transition-all duration-150 ${
                selectedProjectId === project.id
                  ? 'bg-brand-900/30 border-brand-500/50 text-slate-100'
                  : 'bg-slate-900/50 border-slate-800 hover:bg-slate-900 text-slate-300'
              }`}
            >
              <h4 className="text-sm font-semibold">{project.name}</h4>
              {project.description && <p className="text-xs text-slate-400 mt-1 line-clamp-1">{project.description}</p>}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
