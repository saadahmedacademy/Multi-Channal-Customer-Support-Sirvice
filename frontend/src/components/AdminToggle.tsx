'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import Link from 'next/link';

export default function AdminToggle() {
  const { isAdmin, isAdminMode, loading, enableAdmin, disableAdmin } = useAuth();
  const [toggled, setToggled] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleToggle = () => {
    if (isAdminMode) {
      disableAdmin();
      setToggled(false);
      setApiKey('');
      setError('');
      return;
    }
    setToggled(true);
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim()) return;
    setSubmitting(true);
    setError('');

    const ok = await enableAdmin(apiKey.trim());
    if (ok) {
      setToggled(false);
      setApiKey('');
    } else {
      setError('Invalid API key');
    }
    setSubmitting(false);
  };

  const handleClose = () => {
    setToggled(false);
    setApiKey('');
    setError('');
  };

  return (
    <>
      <div className="flex items-center space-x-2">
        {isAdminMode && (
          <Link
            href="/admin"
            className="px-3 py-2 text-xs font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg"
          >
            Dashboard
          </Link>
        )}
        <button
          onClick={handleToggle}
          disabled={loading}
          className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
            isAdminMode
              ? 'bg-gradient-to-r from-indigo-600 to-purple-600'
              : 'bg-gray-300 dark:bg-gray-600'
          }`}
          role="switch"
          aria-checked={isAdminMode}
          aria-label="Admin mode"
        >
          <span
            className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-lg transition-transform duration-300 ${
              isAdminMode ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400 hidden sm:inline">
          {isAdminMode ? 'Admin' : 'Admin'}
        </span>
      </div>

      {toggled && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={handleClose}>
          <div
            className="relative w-full max-w-md mx-4 backdrop-blur-xl bg-white/90 dark:bg-gray-800/90 rounded-2xl shadow-2xl border border-white/20 dark:border-gray-700/50 p-8"
            onClick={e => e.stopPropagation()}
          >
            <button
              onClick={handleClose}
              className="absolute top-4 right-4 p-1 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <div className="flex items-center space-x-3 mb-6">
              <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Admin Access</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">Enter your API key to enable admin mode</p>
              </div>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-700 dark:text-red-300 flex items-center space-x-2">
                <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="adminApiKey" className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">
                  API Key
                </label>
                <input
                  id="adminApiKey"
                  type="password"
                  value={apiKey}
                  onChange={e => setApiKey(e.target.value)}
                  placeholder="Enter your API key"
                  className="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-600 bg-white/50 dark:bg-gray-700/50 text-gray-900 dark:text-white rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all backdrop-blur-sm"
                  autoFocus
                />
              </div>

              <button
                type="submit"
                disabled={submitting || !apiKey.trim()}
                className="w-full py-3 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-bold hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
              >
                {submitting ? (
                  <span className="flex items-center justify-center space-x-2">
                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    <span>Verifying...</span>
                  </span>
                ) : (
                  'Enable Admin Mode'
                )}
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
