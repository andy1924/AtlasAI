'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Radio, AlertOctagon, Box, BarChart3, PlayCircle } from 'lucide-react';

const NAV_ITEMS = [
  { href: '/', label: 'Overview', icon: LayoutDashboard },
  { href: '/threats', label: 'Live Threat Feed', icon: Radio },
  { href: '/incidents', label: 'Incidents', icon: AlertOctagon },
  { href: '/containers', label: 'Containers', icon: Box },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/demo', label: 'Attack Simulator', icon: PlayCircle, highlight: true },
];

export const Sidebar = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950/50 flex flex-col justify-between p-4 min-h-[calc(100vh-4rem)]">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
          SOC Operations
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition font-medium ${
                isActive
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                  : item.highlight
                  ? 'bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 border border-amber-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
              {item.highlight && (
                <span className="ml-auto text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono">
                  DEMO
                </span>
              )}
            </Link>
          );
        })}
      </div>

      <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/40 text-xs text-slate-400 space-y-1 font-mono">
        <div className="text-slate-300 font-semibold">CloudGuard Pipeline</div>
        <div className="text-[11px]">eBPF / Falco → Rules → ML → Correlate → Respond</div>
      </div>
    </aside>
  );
};
