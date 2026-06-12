'use client';

import React, { useState } from 'react';
import { useToast } from '@/lib/toast';

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

const PHONE_REGEX = /^\+[1-9]\d{1,14}$/;

function IdentifierIcon({ type }: { type: string }) {
  const icons: Record<string, React.ReactNode> = {
    email: (
      <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
    phone: (
      <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
      </svg>
    ),
    whatsapp: (
      <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
      </svg>
    ),
  };
  return <span className="mr-3">{icons[type] || <span className="mr-3 text-lg">{type}</span>}</span>;
}

function IdentifierLabel({ type }: { type: string }) {
  const labels: Record<string, string> = {
    email: 'Email',
    phone: 'Phone',
    whatsapp: 'WhatsApp',
  };
  return <>{labels[type] || type}</>;
}

export default function CustomerLinker() {
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [status, setStatus] = useState<'idle' | 'linking' | 'success' | 'error'>('idle');
  const [result, setResult] = useState<LinkResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { showToast } = useToast();

  const handleLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setStatus('linking');

    if (!email && !phone) {
      setError('Please provide at least one identifier (email or phone)');
      setStatus('error');
      return;
    }

    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Please enter a valid email address');
      setStatus('error');
      return;
    }

    if (phone && !PHONE_REGEX.test(phone)) {
      setError('Invalid phone format. Use E.164 format (e.g., +14155551234)');
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
      showToast('Identifiers linked successfully!', 'success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to link identifiers');
      setStatus('error');
    }
  };

  const isValidPhone = !phone || PHONE_REGEX.test(phone);

  if (status === 'success' && result) {
    return (
      <div className="w-full max-w-2xl mx-auto backdrop-blur-md bg-white/60 dark:bg-gray-800/60 rounded-2xl shadow-2xl border border-white/20 dark:border-gray-700/50 p-8">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-green-400 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-2xl shadow-green-500/50">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 dark:from-green-400 dark:via-emerald-400 dark:to-teal-400 bg-clip-text text-transparent mb-2">
            Identifiers Linked
          </h2>
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
                  <IdentifierIcon type={identifier.identifier_type} />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {identifier.identifier_value}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                      <IdentifierLabel type={identifier.identifier_type} />
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
          className="mt-4 w-full py-3 px-4 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white rounded-xl hover:from-indigo-700 hover:via-purple-700 hover:to-pink-700 transition-all font-bold"
        >
          Link Another Customer
        </button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-2xl mx-auto backdrop-blur-md bg-white/60 dark:bg-gray-800/60 rounded-2xl shadow-2xl border border-white/20 dark:border-gray-700/50 p-8">
      <h2 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 dark:from-indigo-400 dark:via-purple-400 dark:to-pink-400 bg-clip-text text-transparent mb-2">
        Link Customer Identifiers
      </h2>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Connect a customer's email and phone number to enable cross-channel continuity. 
        This ensures the AI recognizes the same customer across Web, WhatsApp, and Email channels.
      </p>

      {error && (
        <div className="mb-4 p-4 bg-gradient-to-r from-red-50 to-pink-50 dark:from-red-900/20 dark:to-pink-900/20 border border-red-200/50 dark:border-red-800/50 rounded-xl text-red-700 dark:text-red-300 flex items-center space-x-3 animate-shake">
          <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <span className="font-medium">{error}</span>
        </div>
      )}

      <form onSubmit={handleLink} className="space-y-6">
        <div className="group">
          <label htmlFor="email" className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2 flex items-center space-x-2">
            <svg className="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <span>Email Address</span>
          </label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="customer@example.com"
            className="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-600 bg-white/50 dark:bg-gray-700/50 text-gray-900 dark:text-white rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-300 placeholder-gray-400 dark:placeholder-gray-500 backdrop-blur-sm"
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Enter the customer's email address from web form or email channel
          </p>
        </div>

        <div className="group">
          <label htmlFor="phone" className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2 flex items-center space-x-2">
            <svg className="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            <span>Phone Number</span>
          </label>
          <input
            type="tel"
            id="phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+14155551234"
            className={`w-full px-4 py-3 border-2 bg-white/50 dark:bg-gray-700/50 text-gray-900 dark:text-white rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-300 placeholder-gray-400 dark:placeholder-gray-500 backdrop-blur-sm ${
              phone && !isValidPhone
                ? 'border-red-300 dark:border-red-700'
                : 'border-gray-200 dark:border-gray-600'
            }`}
          />
          {phone && !isValidPhone && (
            <p className="mt-1 text-xs text-red-500 dark:text-red-400">
              Invalid format. Use E.164 format (e.g., +14155551234)
            </p>
          )}
          {phone && isValidPhone && (
            <p className="mt-1 text-xs text-green-500 dark:text-green-400">
              Valid phone format
            </p>
          )}
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Enter the customer's phone number from WhatsApp channel (E.164 format)
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
          className={`w-full py-3 px-4 rounded-xl font-bold text-white transition-all duration-300 transform ${
            status === 'linking' || (!email && !phone)
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-700 hover:via-purple-700 hover:to-pink-700 hover:scale-105 shadow-lg'
          }`}
        >
          {status === 'linking' ? (
            <span className="flex items-center justify-center space-x-3">
              <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span>Linking...</span>
            </span>
          ) : (
            <span className="flex items-center justify-center space-x-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              <span>Link Identifiers</span>
            </span>
          )}
        </button>
      </form>
    </div>
  );
}
