'use client';

import { useState, useCallback } from 'react';
import SupportForm from '@/components/SupportForm';
import TicketStatus from '@/components/TicketStatus';
import { useTheme } from '@/components/ThemeProvider';

const CATEGORY_DESCRIPTIONS = {
  'Technical Support': 'Get help with technical issues, software bugs, integration problems, API errors, and system configurations.',
  'Billing Inquiries': 'Questions about invoices, payments, subscriptions, refunds, and account billing details.',
  'Bug Reports': 'Report software bugs, unexpected behavior, errors, crashes, or any issues you encounter while using our service.',
  'Feature Requests': 'Suggest new features, improvements, or enhancements you would like to see in our product.',
  'General Questions': 'Any other questions about our service, policies, documentation, or general information.'
};

const CATEGORIES = Object.keys(CATEGORY_DESCRIPTIONS);

export default function Home() {
  const [activeTab, setActiveTab] = useState<'submit' | 'check'>('submit');
  const [hoveredCategory, setHoveredCategory] = useState<string | null>(null);
  const { theme, toggleTheme } = useTheme();

  const handleTabKeyDown = useCallback((e: React.KeyboardEvent, tab: 'submit' | 'check') => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      setActiveTab(tab === 'submit' ? 'check' : 'submit');
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 dark:from-gray-900 dark:via-purple-900/20 dark:to-gray-900 transition-all duration-500">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-300/30 dark:bg-purple-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-300/30 dark:bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      {/* Header with Glassmorphism */}
      <header className="relative backdrop-blur-md bg-white/70 dark:bg-gray-800/70 border-b border-white/20 dark:border-gray-700/50 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 dark:from-indigo-400 dark:via-purple-400 dark:to-pink-400 bg-clip-text text-transparent animate-gradient">
                AI Support Center
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-300 font-medium">
                ✨ Get help from our AI-powered support team, available 24/7
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold bg-gradient-to-r from-green-400 to-emerald-500 text-white shadow-lg shadow-green-500/50 dark:shadow-green-500/30 transform hover:scale-105 transition-transform">
                <span className="w-2 h-2 mr-2 bg-white rounded-full animate-pulse"></span>
                Online
              </span>
              <button
                onClick={toggleTheme}
                className="p-3 rounded-xl bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 hover:shadow-lg transform hover:scale-110 transition-all duration-300 group"
                aria-label="Toggle dark mode"
              >
                {theme === 'dark' ? (
                  <svg className="w-5 h-5 text-yellow-500 group-hover:rotate-180 transition-transform duration-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5 text-indigo-600 group-hover:rotate-180 transition-transform duration-500" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation with ARIA */}
      <div className="relative backdrop-blur-md bg-white/50 dark:bg-gray-800/50 border-b border-white/20 dark:border-gray-700/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-2" role="tablist" aria-label="Support options">
            <button
              role="tab"
              aria-selected={activeTab === 'submit'}
              aria-controls="panel-submit"
              id="tab-submit"
              onClick={() => setActiveTab('submit')}
              onKeyDown={(e) => handleTabKeyDown(e, 'submit')}
              className={`relative py-4 px-6 font-semibold text-sm transition-all duration-300 ${
                activeTab === 'submit'
                  ? 'text-indigo-600 dark:text-indigo-400'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              <span className="relative z-10 flex items-center space-x-2">
                <svg className="w-5 h-5 sm:mr-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span className="hidden sm:inline">Submit Request</span>
              </span>
              {activeTab === 'submit' && (
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-t-full animate-slide-in"></div>
              )}
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'check'}
              aria-controls="panel-check"
              id="tab-check"
              onClick={() => setActiveTab('check')}
              onKeyDown={(e) => handleTabKeyDown(e, 'check')}
              className={`relative py-4 px-6 font-semibold text-sm transition-all duration-300 ${
                activeTab === 'check'
                  ? 'text-indigo-600 dark:text-indigo-400'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              <span className="relative z-10 flex items-center space-x-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <span className="hidden sm:inline">Check Status</span>
              </span>
              {activeTab === 'check' && (
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-t-full animate-slide-in"></div>
              )}
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main id="main-content" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Support Form or Ticket Status - preserve state with hidden */}
          <div className="lg:col-span-2">
            <div role="tabpanel" id="panel-submit" aria-labelledby="tab-submit" className={activeTab === 'submit' ? '' : 'hidden'}>
              <SupportForm />
            </div>
            <div role="tabpanel" id="panel-check" aria-labelledby="tab-check" className={activeTab === 'check' ? '' : 'hidden'}>
              <TicketStatus />
            </div>
          </div>

          {/* Info Sidebar with Modern Cards */}
          <div className="space-y-6">
            {/* Response Time Card */}
            <div className="group backdrop-blur-md bg-white/60 dark:bg-gray-800/60 rounded-2xl shadow-xl border border-white/20 dark:border-gray-700/50 p-6 hover:shadow-2xl hover:scale-105 transition-all duration-300">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Response Times</h3>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-xl bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-200/50 dark:border-green-700/50">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-200">AI Response</span>
                  </div>
                  <span className="text-sm font-bold text-green-600 dark:text-green-400">&lt; 2 min</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200/50 dark:border-blue-700/50">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Human Agent</span>
                  </div>
                  <span className="text-sm font-bold text-blue-600 dark:text-blue-400">&lt; 1 hour</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-gradient-to-r from-orange-50 to-amber-50 dark:from-orange-900/20 dark:to-amber-900/20 border border-orange-200/50 dark:border-orange-700/50">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Urgent Issues</span>
                  </div>
                  <span className="text-sm font-bold text-orange-600 dark:text-orange-400">Priority</span>
                </div>
              </div>
            </div>

            {/* Categories Card */}
            <div className="group backdrop-blur-md bg-white/60 dark:bg-gray-800/60 rounded-2xl shadow-xl border border-white/20 dark:border-gray-700/50 p-6 hover:shadow-2xl hover:scale-105 transition-all duration-300">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Support Categories</h3>
              </div>
              <ul className="space-y-3">
                {CATEGORIES.map((category) => (
                  <li
                    key={category}
                    className="relative flex items-center text-sm text-gray-700 dark:text-gray-200 p-2 rounded-lg hover:bg-white/50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800"
                    onMouseEnter={() => setHoveredCategory(category)}
                    onMouseLeave={() => setHoveredCategory(null)}
                    onFocus={() => setHoveredCategory(category)}
                    onBlur={() => setHoveredCategory(null)}
                    tabIndex={0}
                    role="button"
                    aria-describedby={hoveredCategory === category ? `cat-desc-${category.replace(/\s+/g, '-')}` : undefined}
                  >
                    <span className={`w-3 h-3 mr-3 rounded-full shadow-lg ${
                      category === 'Technical Support' ? 'bg-gradient-to-br from-blue-400 to-blue-600 shadow-blue-500/50' :
                      category === 'Billing Inquiries' ? 'bg-gradient-to-br from-green-400 to-green-600 shadow-green-500/50' :
                      category === 'Bug Reports' ? 'bg-gradient-to-br from-purple-400 to-purple-600 shadow-purple-500/50' :
                      category === 'Feature Requests' ? 'bg-gradient-to-br from-yellow-400 to-yellow-600 shadow-yellow-500/50' :
                      'bg-gradient-to-br from-gray-400 to-gray-600 shadow-gray-500/50'
                    }`}></span>
                    <span className="font-medium">{category}</span>
                    {hoveredCategory === category && (
                      <div
                        id={`cat-desc-${category.replace(/\s+/g, '-')}`}
                        className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-3 bg-gray-900 dark:bg-gray-800 text-white text-xs rounded-lg shadow-2xl z-50 border border-gray-700 md:bottom-auto md:left-auto md:right-full md:top-1/2 md:transform md:translate-x-0 md:-translate-y-1/2 md:mb-0 md:mr-2"
                        role="tooltip"
                      >
                        <div className="absolute top-full left-1/2 transform -translate-x-1/2 -translate-y-1 w-2 h-2 bg-gray-900 dark:bg-gray-800 rotate-45 border-b border-r border-gray-700 md:hidden"></div>
                        <div className="hidden md:block absolute right-0 top-1/2 transform translate-x-1 -translate-y-1/2 w-2 h-2 bg-gray-900 dark:bg-gray-800 rotate-45 border-r border-t border-gray-700"></div>
                        {CATEGORY_DESCRIPTIONS[category as keyof typeof CATEGORY_DESCRIPTIONS]}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>

            {/* Contact Info Card */}
            <div className="group backdrop-blur-md bg-white/60 dark:bg-gray-800/60 rounded-2xl shadow-xl border border-white/20 dark:border-gray-700/50 p-6 hover:shadow-2xl hover:scale-105 transition-all duration-300">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Contact Us</h3>
              </div>
              <div className="space-y-3">
                <a href="mailto:lasanitech7@gmail.com" className="flex items-center text-sm text-gray-700 dark:text-gray-200 p-3 rounded-lg hover:bg-gradient-to-r hover:from-indigo-50 hover:to-purple-50 dark:hover:from-indigo-900/20 dark:hover:to-purple-900/20 transition-all group/item">
                  <div className="p-2 bg-gradient-to-br from-indigo-100 to-purple-100 dark:from-indigo-900/50 dark:to-purple-900/50 rounded-lg mr-3 group-hover/item:scale-110 transition-transform">
                    <svg className="w-4 h-4 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <span className="font-medium">lasanitech7@gmail.com</span>
                </a>
                <a href="https://wa.me/1234567890" className="flex items-center text-sm text-gray-700 dark:text-gray-200 p-3 rounded-lg hover:bg-gradient-to-r hover:from-green-50 hover:to-emerald-50 dark:hover:from-green-900/20 dark:hover:to-emerald-900/20 transition-all group/item">
                  <div className="p-2 bg-gradient-to-br from-green-100 to-emerald-100 dark:from-green-900/50 dark:to-emerald-900/50 rounded-lg mr-3 group-hover/item:scale-110 transition-transform">
                    <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <span className="font-medium">WhatsApp: +1 234 567 8900</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Modern Footer */}
      <footer className="relative backdrop-blur-md bg-white/50 dark:bg-gray-800/50 border-t border-white/20 dark:border-gray-700/50 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300">
                © 2026 AI Support Center. <span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent font-bold">Powered by AI</span>, backed by humans.
              </p>
            </div>
            <div className="flex space-x-6">
              <a href="/privacy" className="text-sm text-gray-600 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors font-medium">
                Privacy Policy
              </a>
              <a href="/terms" className="text-sm text-gray-600 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors font-medium">
                Terms of Service
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
