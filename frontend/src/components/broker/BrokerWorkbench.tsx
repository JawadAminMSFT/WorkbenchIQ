'use client';

import React, { useState } from 'react';
import { Briefcase } from 'lucide-react';
import BrokerDashboard from './BrokerDashboard';
import ClientWorkspace from './ClientWorkspace';

interface BrokerWorkbenchProps {
  applicationId?: string;
}

export default function BrokerWorkbench({ applicationId }: BrokerWorkbenchProps) {
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Header — always visible */}
      <div className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
            <Briefcase className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-slate-900">
              Commercial Brokerage Workbench
            </h1>
            <p className="text-sm text-slate-500">
              {applicationId ? `Application ${applicationId}` : 'Manage clients, submissions & quotes'}
            </p>
          </div>
        </div>
      </div>

      {/* View switcher */}
      {!selectedClientId ? (
        <BrokerDashboard onSelectClient={setSelectedClientId} />
      ) : (
        <ClientWorkspace
          clientId={selectedClientId}
          onBack={() => setSelectedClientId(null)}
        />
      )}
    </div>
  );
}
