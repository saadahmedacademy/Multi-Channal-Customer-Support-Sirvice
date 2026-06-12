'use client';

import React, { useState, useEffect } from 'react';

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

export default function TicketStatus() {
  const [ticketId, setTicketId] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [ticketData, setTicketData] = useState<TicketStatusData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copyNotification, setCopyNotification] = useState<{show: boolean; text: string}>({show: false, text: ''});

  const copyToClipboard = async (text: string, label: string = 'Copied!') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopyNotification({show: true, text: label});
      setTimeout(() => setCopyNotification({show: false, text: ''}), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
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

  if (status === 'success' && ticketData) {
    return (
      <div className="w-full max-w-4xl mx-auto p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md relative">
        {/* Copy Notification Toast */}
        {copyNotification.show && (
          <div className="fixed top-6 left-1/2 transform -translate-x-1/2 z-50 animate-fade-in-down">
            <div className="bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center space-x-2">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="font-medium">{copyNotification.text}</span>
            </div>
          </div>
        )}

        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Ticket: {ticketData.ticket_id}
              </h2>
              <button
                onClick={() => copyToClipboard(ticketData.ticket_id, 'Ticket ID copied!')}
                className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
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
                        onClick={() => copyToClipboard(message.content, 'Copied!')}
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
          className="mt-6 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Check Another Ticket
        </button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Check Ticket Status</h2>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Enter your ticket ID to view the status and conversation history.
      </p>

      {error && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="ticketId" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
            Ticket ID
          </label>
          <input
            type="text"
            id="ticketId"
            value={ticketId}
            onChange={(e) => setTicketId(e.target.value.toUpperCase())}
            placeholder="TICKET-XXXXXX"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent uppercase"
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Format: TICKET-XXXXXXXX or full UUID
          </p>
        </div>

        <button
          type="submit"
          disabled={status === 'loading' || !ticketId.trim()}
          className={`w-full py-2 px-4 rounded-lg font-medium text-white transition-colors ${
            status === 'loading'
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {status === 'loading' ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Checking...
            </span>
          ) : (
            'Check Status'
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
