'use client';

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const COLORS = ['#6366f1', '#10b981', '#f59e0b'];

interface ChannelDistributionProps {
  data: { name: string; value: number }[];
}

export default function ChannelDistribution({ data }: ChannelDistributionProps) {
  if (!data.length) {
    return (
      <div className="backdrop-blur-md bg-white/60 dark:bg-gray-800/60 rounded-2xl shadow-xl border border-white/20 dark:border-gray-700/50 p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Channel Distribution</h3>
        <p className="text-gray-400 text-sm">No data yet</p>
      </div>
    );
  }

  return (
    <div className="backdrop-blur-md bg-white/60 dark:bg-gray-800/60 rounded-2xl shadow-xl border border-white/20 dark:border-gray-700/50 p-6">
      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Channel Distribution</h3>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie data={data} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={4} dataKey="value">
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255,255,255,0.9)',
              borderRadius: '12px',
              border: '1px solid #e5e7eb',
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
