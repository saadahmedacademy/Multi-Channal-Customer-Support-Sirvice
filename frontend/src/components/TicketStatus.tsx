'use client';

import React, { useState, useEffect } from 'react';
import { copyToClipboard, fallbackCopy } from '@/lib/clipboard';
import { useToast } from '@/lib/toast';

interface Message {
  id: string;
  role: 'customer' | 'agent' | 'system';
  content: string;
  created_at: string;
}

interface TicketStatusData {
  ticket_id: string;
  status: 'open' | 'in_progress' | 'resolved' | 'escalated' | 'closed';
  category: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  resolved_at: string | null;
  messages: Message[];
  resolution_notes: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  open: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  in_progress: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  resolved: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  escalated: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  closed: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
};

const PRIORITY_COLORS: Record<string, string> = {
  low: 'bg-gray-100 text-gray-700 dark:bg-gray-600 dark:text-gray-200',
  medium: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200',
  high: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-200',
  critical: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200'
};

const TICKET_ID_REGEX = /^TICKET-[A-Z0-9]{6,}$/;

export default function TicketStatus() {
  const [ticketId, setTicketId] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [ticketData, setTicketData] = useState<TicketStatusData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { showToast } = useToast();

  const handleCopy = async (text: string, label: string = 'Copied!') => {
    const ok = await copyToClipboard(text);
    if (ok) {
      showToast(label, 'success');
    } else {
      const fallbackOk = fallbackCopy(text);
      if (fallbackOk) {
        showToast(label, 'success');
      } else {
        showToast('Could not copy. Please select the text manually.', 'error');
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setStatus('loading');

    try {
      const response = await fetch(`/api/ticket/${ticketId}`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ticket not found');
      }

      const data = await response.json();
      setTicketData(data);
      setStatus('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch ticket status');
      setStatus('error');
    }
  };

  useEffect(() => {
    if (status === 'success') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [status]);

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isValidTicketId = TICKET_ID_REGEX.test(ticketId);

  if (status === 'success' && ticketData) {
    return (
      <div className="w-full max-w-4xl mx-auto backdrop-blur-md bg-white/60 dark:bg-gray-800/60 rounded-2xl shadow-2xl border border-white/20 dark:border-gray-700/50 p-8">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Ticket: {ticketData.ticket_id}
              </h2>
              <button
                onClick={() => handleCopy(ticketData.ticket_id, 'Ticket ID copied!')}
                className="p-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-lg transition-all transform hover:scale-110"
                title="Copy to clipboard"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${STATUS_COLORS[ticketData.status]}`}>
              {ticketData.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
              <p className="text-xs text-gray-500 dark:text-gray-400">Category</p>
              <p className="font-medium text-gray-900 dark:text-white capitalize">{ticketData.category}</p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
              <p className="text-xs text-gray-500 dark:text-gray-400">Priority</p>
              <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${PRIORITY_COLORS[ticketData.priority]}`}>
                {ticketData.priority.toUpperCase()}
              </span>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
              <p className="text-xs text-gray-500 dark:text-gray-400">Created</p>
              <p className="font-medium text-gray-900 dark:text-white">{formatDateTime(ticketData.created_at)}</p>
            </div>
            {ticketData.resolved_at && (
              <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
                <p className="text-xs text-gray-500 dark:text-gray-400">Resolved</p>
                <p className="font-medium text-gray-900 dark:text-white">{formatDateTime(ticketData.resolved_at)}</p>
              </div>
            )}
          </div>

          {ticketData.resolution_notes && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-4">
              <p className="text-sm font-medium text-green-800 dark:text-green-300">Resolution Notes</p>
              <p className="text-sm text-green-700 dark:text-green-400 mt-1">{ticketData.resolution_notes}</p>
            </div>
          )}
        </div>

        <div className="border-t dark:border-gray-700 pt-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Conversation</h3>
          <div className="space-y-4">
            {ticketData.messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'customer' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    message.role === 'customer'
                      ? 'bg-blue-600 text-white'
                      : message.role === 'system'
                      ? 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-200'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-xs font-medium ${
                      message.role === 'customer' ? 'text-blue-100' : 'text-gray-500 dark:text-gray-400'
                    }`}>
                      {message.role === 'customer' ? 'You' : message.role === 'agent' ? 'Support Agent' : 'System'}
                    </span>
                    <span className="flex items-center space-x-2">
                      <span className={`text-xs ${
                        message.role === 'customer' ? 'text-blue-100' : 'text-gray-400 dark:text-gray-500'
                      }`}>
                        {new Date(message.created_at).toLocaleTimeString()}
                      </span>
                      <button
                        onClick={() => handleCopy(message.content, 'Copied!')}
                        className={`p-1 rounded transition-colors ${
                          message.role === 'customer'
                            ? 'hover:bg-blue-500 text-blue-100'
                            : 'hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-400 dark:text-gray-500'
                        }`}
                        title="Copy message"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      </button>
                    </span>
                  </div>
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={() => {
            setStatus('idle');
            setTicketId('');
            setTicketData(null);
          }}
          className="mt-6 w-full py-3 px-4 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white rounded-xl hover:from-indigo-700 hover:via-purple-700 hover:to-pink-700 transition-all font-bold"
        >
          Check Another Ticket
        </button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto backdrop-blur-md bg-white/60 dark:bg-gray-800/60 rounded-2xl shadow-2xl border border-white/20 dark:border-gray-700/50 p-8">
      <h2 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 dark:from-indigo-400 dark:via-purple-400 dark:to-pink-400 bg-clip-text text-transparent mb-2">
        Check Ticket Status
      </h2>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Enter your ticket ID to view the status and conversation history.
      </p>

      {error && (
        <div className="mb-4 p-4 bg-gradient-to-r from-red-50 to-pink-50 dark:from-red-900/20 dark:to-pink-900/20 border border-red-200/50 dark:border-red-800/50 rounded-xl text-red-700 dark:text-red-300 flex items-center space-x-3 animate-shake">
          <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <span className="font-medium">{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="ticketId" className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2 flex items-center space-x-2">
            <svg className="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
            </svg>
            <span>Ticket ID</span>
          </label>
          <input
            type="text"
            id="ticketId"
            value={ticketId}
            onChange={(e) => setTicketId(e.target.value.toUpperCase())}
            onPaste={(e) => {
              const pasted = e.clipboardData.getData('text');
              const cleaned = pasted.trim().toUpperCase();
              setTicketId(cleaned);
              e.preventDefault();
            }}
            onBlur={(e) => setTicketId(e.target.value.trim().toUpperCase())}
            placeholder="TICKET-XXXXXX"
            className={`w-full px-4 py-3 border-2 bg-white/50 dark:bg-gray-700/50 text-gray-900 dark:text-white rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-300 backdrop-blur-sm uppercase ${
              ticketId && !isValidTicketId
                ? 'border-red-300 dark:border-red-700'
                : 'border-gray-200 dark:border-gray-600'
            }`}
          />
          {ticketId && !isValidTicketId && (
            <p className="mt-1 text-xs text-red-500 dark:text-red-400">
              Invalid format. Expected: TICKET-XXXXXXXX
            </p>
          )}
          {isValidTicketId && (
            <p className="mt-1 text-xs text-green-500 dark:text-green-400">
              Valid ticket ID format
            </p>
          )}
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Format: TICKET-XXXXXXXX or full UUID
          </p>
        </div>

        <button
          type="submit"
          disabled={status === 'loading' || !ticketId.trim()}
          className={`w-full py-3 px-4 rounded-xl font-bold text-white transition-all duration-300 transform ${
            status === 'loading' || !ticketId.trim()
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-700 hover:via-purple-700 hover:to-pink-700 hover:scale-105 shadow-lg'
          }`}
        >
          {status === 'loading' ? (
            <span className="flex items-center justify-center space-x-3">
              <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span>Checking...</span>
            </span>
          ) : (
            <span className="flex items-center justify-center space-x-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Check Status</span>
            </span>
          )}
        </button>
      </form>

      <div className="mt-6 pt-6 border-t dark:border-gray-700">
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          Your ticket ID was provided when you submitted your support request.
          Check your email or confirmation message.
        </p>
      </div>
    </div>
  );
}
