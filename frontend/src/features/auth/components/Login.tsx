import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { apiClient } from '../../../lib/api-client';
import { useAuthStore } from '../../../stores/authStore';

export const Login: React.FC = () => {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const login = useAuthStore((state) => state.login);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const onSubmit = async (data: any) => {
    setIsLoading(true);
    setApiError(null);
    try {
      const params = new URLSearchParams();
      params.append('username', data.email);
      params.append('password', data.password);

      const response = await apiClient.post('/auth/login', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      login(response.data.access_token);
    } catch (err: any) {
      setApiError(err.response?.data?.detail || 'Authentication failed. Please check credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[80vh]">
      <div className="w-full max-w-md p-8 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl">
        <h2 className="text-3xl font-extrabold tracking-tight text-center text-slate-100 mb-2">
          HIR AI Platform
        </h2>
        <p className="text-slate-400 text-center text-sm mb-6">
          Human Intelligent Review Platform
        </p>

        {apiError && (
          <div className="p-3 mb-4 text-sm text-red-400 bg-red-950/50 border border-red-900/50 rounded-lg">
            {apiError}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Email Address</label>
            <input
              type="email"
              {...register('email', { required: 'Email is required' })}
              className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-200"
              placeholder="name@company.com"
            />
            {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message as string}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Password</label>
            <input
              type="password"
              {...register('password', { required: 'Password is required' })}
              className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-200"
              placeholder="••••••••"
            />
            {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message as string}</p>}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 mt-2 bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white font-semibold rounded-lg shadow transition-all duration-200 focus:outline-none disabled:opacity-50"
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
};
