'use client';

import { useEffect, useState, useRef } from 'react';

interface StatsCardsProps {
  totalTickets: number;
  openTickets: number;
  resolvedToday: number;
  avgResponseMinutes: number;
}

function AnimatedCounter({ value, suffix = '' }: { value: number; suffix?: string }) {
  const [display, setDisplay] = useState(0);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const duration = 1000;
    const steps = 30;
    const increment = value / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= value) {
        setDisplay(value);
        clearInterval(timer);
      } else {
        setDisplay(Math.floor(current));
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [value]);

  return <>{display}{suffix}</>;
}

export default function StatsCards({ totalTickets, openTickets, resolvedToday, avgResponseMinutes }: StatsCardsProps) {
  const cards = [
    {
      label: 'Total Tickets',
      value: totalTickets,
      suffix: '',
      gradient: 'from-blue-500 to-indigo-600',
      shadow: 'shadow-blue-500/30',
      icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
    },
    {
      label: 'Open Tickets',
      value: openTickets,
      suffix: '',
      gradient: 'from-amber-500 to-orange-600',
      shadow: 'shadow-orange-500/30',
      icon: 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    },
    {
      label: 'Resolved Today',
      value: resolvedToday,
      suffix: '',
      gradient: 'from-emerald-500 to-green-600',
      shadow: 'shadow-green-500/30',
      icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    },
    {
      label: 'Avg Response',
      value: avgResponseMinutes,
      suffix: 'm',
      gradient: 'from-purple-500 to-pink-600',
      shadow: 'shadow-pink-500/30',
      icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(card => (
        <div
          key={card.label}
          className="backdrop-blur-md bg-white/60 dark:bg-gray-800/60 rounded-2xl shadow-xl border border-white/20 dark:border-gray-700/50 p-5 hover:shadow-2xl hover:scale-[1.02] transition-all duration-300"
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{card.label}</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                <AnimatedCounter value={card.value} suffix={card.suffix} />
              </p>
            </div>
            <div className={`p-3 bg-gradient-to-br ${card.gradient} rounded-xl ${card.shadow} shadow-lg`}>
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={card.icon} />
              </svg>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
