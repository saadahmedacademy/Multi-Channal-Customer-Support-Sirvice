'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface TicketTrendChartProps {
  data: { date: string; total: number }[];
}

export default function TicketTrendChart({ data }: TicketTrendChartProps) {
  const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));

  return (
    <div className="backdrop-blur-md bg-white/60 dark:bg-gray-800/60 rounded-2xl shadow-xl border border-white/20 dark:border-gray-700/50 p-6">
      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Ticket Trend (Last 7 Days)</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={sorted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#9ca3af" />
          <YAxis allowDecimals={false} tick={{ fontSize: 12 }} stroke="#9ca3af" />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255,255,255,0.9)',
              borderRadius: '12px',
              border: '1px solid #e5e7eb',
            }}
          />
          <Line type="monotone" dataKey="total" stroke="#6366f1" strokeWidth={3} dot={{ fill: '#6366f1', r: 5 }} activeDot={{ r: 7 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
