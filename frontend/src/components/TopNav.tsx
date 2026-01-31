'use client';

import Link from 'next/link';
import {
  LayoutDashboard,
  Clock,
  FileText,
  FileStack,
  Settings,
  ChevronDown,
} from 'lucide-react';
import type { ApplicationListItem, ApplicationMetadata } from '@/lib/types';
import clsx from 'clsx';
import { useState } from 'react';
import PersonaSelector from './PersonaSelector';
import { usePersona } from '@/lib/PersonaContext';

interface TopNavProps {
  applications: ApplicationListItem[];
  selectedAppId?: string;
  selectedApp?: ApplicationMetadata;
  activeView: 'overview' | 'timeline' | 'documents' | 'source';
  onSelectApp: (appId: string) => void;
  onChangeView: (view: 'overview' | 'timeline' | 'documents' | 'source') => void;
}

export default function TopNav({
  applications,
  selectedAppId,
  selectedApp,
  activeView,
  onSelectApp,
  onChangeView,
}: TopNavProps) {
  const [appDropdownOpen, setAppDropdownOpen] = useState(false);
  const { personaConfig } = usePersona();
  
  const hasDocuments = selectedApp?.files && selectedApp.files.length > 0;
  const hasSourcePages = selectedApp?.markdown_pages && selectedApp.markdown_pages.length > 0;
  
  // Automotive claims has its own overview with inline documents/timeline - hide these tabs
  const isAutomotiveClaims = personaConfig.id === 'automotive_claims';

  const navItems = [
    { id: 'overview' as const, label: 'Overview', icon: LayoutDashboard, enabled: true },
    { id: 'timeline' as const, label: 'Timeline', icon: Clock, enabled: true, hidden: isAutomotiveClaims },
    { id: 'documents' as const, label: 'Documents', icon: FileText, enabled: hasDocuments, count: selectedApp?.files?.length, hidden: isAutomotiveClaims },
    { id: 'source' as const, label: 'Source Pages', icon: FileStack, enabled: hasSourcePages, count: selectedApp?.markdown_pages?.length },
  ].filter(item => !item.hidden);

  const selectedApplication = applications.find(a => a.id === selectedAppId);

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      {/* Top Bar */}
      <div className="flex items-center justify-between px-6 py-3">
        {/* Logo & Brand */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2">
            <div 
              className="w-9 h-9 rounded-lg flex items-center justify-center shadow-sm"
              style={{ background: `linear-gradient(135deg, ${personaConfig.primaryColor}, ${personaConfig.accentColor})` }}
            >
              <span className="text-white font-bold text-xs">W.IQ</span>
            </div>
            <span className="font-semibold text-lg text-slate-900">WorkbenchIQ</span>
          </Link>

          {/* Persona Selector */}
          <PersonaSelector />

          {/* Application Selector */}
          {applications.length > 0 && (
            <div className="relative">
              <button
                onClick={() => setAppDropdownOpen(!appDropdownOpen)}
                className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 transition-colors"
              >
                <span className="text-sm font-medium text-slate-700">
                  {selectedApplication?.summary_title || selectedApplication?.id?.substring(0, 8) || 'Select Application'}
                </span>
                <ChevronDown className={clsx('w-4 h-4 text-slate-500 transition-transform', appDropdownOpen && 'rotate-180')} />
              </button>

              {appDropdownOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setAppDropdownOpen(false)} />
                  <div className="absolute top-full left-0 mt-1 w-64 bg-white rounded-lg shadow-lg border border-slate-200 z-20 max-h-96 overflow-y-auto flex flex-col">
                    <div className="py-1 overflow-y-auto">
                      {applications.map((app) => (
                        <button
                          key={app.id}
                          onClick={() => {
                            onSelectApp(app.id);
                            setAppDropdownOpen(false);
                          }}
                          className={clsx(
                            'w-full text-left px-4 py-2 text-sm hover:bg-slate-50 transition-colors',
                            selectedAppId === app.id && 'bg-indigo-50 text-indigo-700'
                          )}
                        >
                          <div className="font-medium truncate">
                            {app.summary_title || app.id.substring(0, 8)}
                          </div>
                          <div className="text-xs text-slate-500 flex items-center gap-2">
                            {app.external_reference || 'No reference'}
                            <span className={clsx(
                              'px-1.5 py-0.5 rounded text-[10px] font-medium',
                              app.status === 'completed' ? 'bg-emerald-100 text-emerald-700' :
                              app.status === 'extracted' ? 'bg-sky-100 text-sky-700' :
                              app.status === 'error' ? 'bg-rose-100 text-rose-700' :
                              'bg-amber-100 text-amber-700'
                            )}>
                              {app.status}
                            </span>
                          </div>
                        </button>
                      ))}
                    </div>
                    <div className="border-t border-slate-200 mt-auto">
                      <Link
                        href="/admin"
                        className="block w-full text-left px-4 py-2 text-sm text-indigo-600 hover:bg-indigo-50 transition-colors"
                        onClick={() => setAppDropdownOpen(false)}
                      >
                        + New Application
                      </Link>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* Right Side Actions */}
        <div className="flex items-center gap-4">
          <Link
            href="/admin"
            className="flex items-center gap-2 px-3 py-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <Settings className="w-4 h-4" />
            <span className="text-sm">Admin</span>
          </Link>
        </div>
      </div>

      {/* Navigation Tabs */}
      {selectedApp && (
        <nav className="flex items-center gap-1 px-6 border-t border-slate-100 bg-slate-50/50">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => item.enabled && onChangeView(item.id)}
              disabled={!item.enabled}
              className={clsx(
                'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors',
                activeView === item.id
                  ? 'border-indigo-500 text-indigo-600 bg-white'
                  : item.enabled
                  ? 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
                  : 'border-transparent text-slate-400 cursor-not-allowed'
              )}
            >
              <item.icon className="w-4 h-4" />
              <span>{item.label}</span>
              {item.count !== undefined && item.count > 0 && (
                <span className="ml-1 px-1.5 py-0.5 bg-slate-200 text-slate-600 text-xs rounded">
                  {item.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      )}
    </header>
  );
}
