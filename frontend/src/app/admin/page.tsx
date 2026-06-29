'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import StatsCards from '@/components/admin/StatsCards';
import TicketTrendChart from '@/components/admin/TicketTrendChart';
import ChannelDistribution from '@/components/admin/ChannelDistribution';

interface MetricsData {
  generated_at: string;
  tickets: {
    by_channel: Record<string, { total: number; by_status: Record<string, number> }>;
    today: Record<string, number>;
  };
  messages: {
    by_channel: Record<string, { inbound: number; outbound: number }>;
  };
  response_times: Record<string, { avg_seconds: number; avg_minutes: number }>;
}

interface TicketSummary {
  period_days: number;
  by_date: Record<string, { total: number; by_channel: Record<string, number>; by_status: Record<string, number> }>;
}

export default function AdminDashboard() {
  const { isAdmin, loading } = useAuth();
  const router = useRouter();
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [summary, setSummary] = useState<TicketSummary | null>(null);
  const [fetchError, setFetchError] = useState('');

  useEffect(() => {
    if (loading) return;
    if (!isAdmin) {
      router.replace('/');
      return;
    }

    Promise.all([
      fetch('/api/admin/metrics').then(r => r.json()),
      fetch('/api/admin/tickets/summary?days=7').then(r => r.json()),
    ])
      .then(([metricsData, summaryData]) => {
        setMetrics(metricsData);
        setSummary(summaryData);
      })
      .catch(() => setFetchError('Failed to load dashboard data'));
  }, [loading, isAdmin, router]);

  if (loading || !metrics) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 dark:from-gray-900 dark:via-purple-900/20 dark:to-gray-900">
        <div className="flex items-center space-x-3">
          <svg className="animate-spin h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="text-gray-600 dark:text-gray-300 font-medium">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  const channelData = metrics
    ? Object.entries(metrics.tickets.by_channel).map(([name, data]) => ({
        name: name.replace('_', ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()),
        value: data.total,
      }))
    : [];

  const trendData = summary
    ? Object.entries(summary.by_date).map(([date, data]) => ({ date, total: data.total }))
    : [];

  const totalTickets = metrics ? Object.values(metrics.tickets.by_channel).reduce((s, c) => s + c.total, 0) : 0;
  const openTickets = metrics
    ? Object.values(metrics.tickets.by_channel).reduce((s, c) => s + (c.by_status['open'] || 0) + (c.by_status['in_progress'] || 0), 0)
    : 0;
  const resolvedToday = metrics ? Object.values(metrics.tickets.today).reduce((s, c) => s + c, 0) : 0;
  const avgMinutes = metrics
    ? Math.round(
        Object.values(metrics.response_times).reduce((s, c) => s + c.avg_minutes, 0) /
          Math.max(Object.keys(metrics.response_times).length, 1),
      )
    : 0;

  const allStatuses: Record<string, number> = {};
  if (metrics) {
    for (const ch of Object.values(metrics.tickets.by_channel)) {
      for (const [status, count] of Object.entries(ch.by_status)) {
        allStatuses[status] = (allStatuses[status] || 0) + count;
      }
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 dark:from-gray-900 dark:via-purple-900/20 dark:to-gray-900">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-300/30 dark:bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-300/30 dark:bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <header className="relative backdrop-blur-md bg-white/70 dark:bg-gray-800/70 border-b border-white/20 dark:border-gray-700/50 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                Admin Dashboard
              </h1>
            </div>
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2 text-sm font-semibold text-gray-600 dark:text-gray-300 bg-white/50 dark:bg-gray-700/50 rounded-xl hover:bg-white/80 dark:hover:bg-gray-700/80 transition-all border border-gray-200 dark:border-gray-600"
            >
              Back to Support
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {fetchError && (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-700 dark:text-red-300 text-sm">
            {fetchError}
          </div>
        )}

        <StatsCards
          totalTickets={totalTickets}
          openTickets={openTickets}
          resolvedToday={resolvedToday}
          avgResponseMinutes={avgMinutes}
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TicketTrendChart data={trendData} />
          <ChannelDistribution data={channelData} />
        </div>

        <div className="backdrop-blur-md bg-white/60 dark:bg-gray-800/60 rounded-2xl shadow-xl border border-white/20 dark:border-gray-700/50 p-6">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Tickets by Status</h3>
          <div className="space-y-3">
            {Object.entries(allStatuses).length === 0 && (
              <p className="text-gray-400 text-sm">No tickets yet</p>
            )}
            {Object.entries(allStatuses).map(([status, count]) => {
              const pct = totalTickets > 0 ? Math.round((count / totalTickets) * 100) : 0;
              const barColor =
                status === 'resolved' || status === 'closed'
                  ? 'bg-gradient-to-r from-emerald-500 to-green-500'
                  : status === 'open' || status === 'in_progress'
                    ? 'bg-gradient-to-r from-amber-500 to-orange-500'
                    : 'bg-gradient-to-r from-red-500 to-pink-500';
              return (
                <div key={status}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium text-gray-700 dark:text-gray-200 capitalize">{status.replace('_', ' ')}</span>
                    <span className="text-gray-500 dark:text-gray-400">{count} ({pct}%)</span>
                  </div>
                  <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-1000 ${barColor}`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {metrics && (
          <div className="backdrop-blur-md bg-white/60 dark:bg-gray-800/60 rounded-2xl shadow-xl border border-white/20 dark:border-gray-700/50 p-6">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Response Times by Channel</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {Object.entries(metrics.response_times).map(([channel, rt]) => (
                <div key={channel} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400 capitalize">{channel.replace('_', ' ')}</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                    {rt.avg_minutes.toFixed(1)} <span className="text-sm font-normal text-gray-400">min</span>
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
