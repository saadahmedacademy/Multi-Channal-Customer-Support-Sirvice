'use client';

import React, { useState } from 'react';

interface LinkedIdentifier {
  id: string;
  identifier_type: string;
  identifier_value: string;
  verified: boolean;
  created_at: string;
}

interface LinkResponse {
  customer_id: string;
  message: string;
  identifiers: LinkedIdentifier[];
}

export default function CustomerLinker() {
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [status, setStatus] = useState<'idle' | 'linking' | 'success' | 'error'>('idle');
  const [result, setResult] = useState<LinkResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setStatus('linking');

    if (!email && !phone) {
      setError('Please provide at least one identifier (email or phone)');
      setStatus('error');
      return;
    }

    try {
      const response = await fetch('/api/customers/link-identifiers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, phone })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to link identifiers');
      }

      const data: LinkResponse = await response.json();
      setResult(data);
      setStatus('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to link identifiers');
      setStatus('error');
    }
  };

  const formatIdentifierType = (type: string) => {
    const types: Record<string, string> = {
      email: '📧 Email',
      phone: '📱 Phone',
      whatsapp: '💬 WhatsApp'
    };
    return types[type] || type;
  };

  if (status === 'success' && result) {
    return (
      <div className="w-full max-w-2xl mx-auto p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Identifiers Linked</h2>
          <p className="text-gray-600 dark:text-gray-300">{result.message}</p>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-4">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Customer ID</p>
          <p className="text-lg font-mono font-bold text-gray-900 dark:text-white">{result.customer_id}</p>
        </div>

        <div className="border-t dark:border-gray-600 pt-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Linked Identifiers</h3>
          <div className="space-y-3">
            {result.identifiers.map((identifier) => (
              <div
                key={identifier.id}
                className="flex items-center justify-between p-3 bg-white dark:bg-gray-600 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <span className="text-xl">{formatIdentifierType(identifier.identifier_type)}</span>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {identifier.identifier_value}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                      {identifier.identifier_type}
                    </p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  identifier.verified
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                }`}>
                  {identifier.verified ? '✓ Verified' : 'Pending'}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            <strong>Cross-Channel Continuity:</strong> This customer will now be recognized across all channels 
            (Web, WhatsApp, Email) with unified conversation history.
          </p>
        </div>

        <button
          onClick={() => {
            setStatus('idle');
            setEmail('');
            setPhone('');
            setResult(null);
          }}
          className="mt-4 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Link Another Customer
        </button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Link Customer Identifiers</h2>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Connect a customer's email and phone number to enable cross-channel continuity. 
        This ensures the AI recognizes the same customer across Web, WhatsApp, and Email channels.
      </p>

      {error && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      <form onSubmit={handleLink} className="space-y-6">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
            Email Address
          </label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="customer@example.com"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Enter the customer's email address from web form or email channel
          </p>
        </div>

        <div>
          <label htmlFor="phone" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
            Phone Number
          </label>
          <input
            type="tel"
            id="phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+14155551234"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Enter the customer's phone number from WhatsApp channel
          </p>
        </div>

        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <p className="text-sm text-yellow-800 dark:text-yellow-200">
            <strong>What happens:</strong>
          </p>
          <ul className="text-sm text-yellow-700 dark:text-yellow-300 mt-2 space-y-1 list-disc list-inside">
            <li>If both identifiers exist separately, they will be merged into one profile</li>
            <li>If only one exists, the other will be added as a linked identifier</li>
            <li>If neither exists, a new customer profile will be created</li>
            <li>All conversation history will be unified under the merged profile</li>
          </ul>
        </div>

        <button
          type="submit"
          disabled={status === 'linking' || (!email && !phone)}
          className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-colors ${
            status === 'linking' || (!email && !phone)
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {status === 'linking' ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Linking...
            </span>
          ) : (
            'Link Identifiers'
          )}
        </button>
      </form>
    </div>
  );
}
