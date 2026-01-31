/**
 * Calculations Panel Component
 * 
 * Displays mortgage calculations with OSFI B-20 stress test:
 * - GDS / TDS ratios (contract and stress test)
 * - LTV ratio
 * - Monthly payment breakdown
 * - Inputs with provenance
 */

'use client';

import React from 'react';
import {
  Calculator, TrendingUp, AlertTriangle, CheckCircle, Info,
  DollarSign, Percent, Home
} from 'lucide-react';
import type {
  MortgageRatios,
  MortgageStressRatios,
  MortgageLoan,
  MortgageIncome,
  MortgageLiabilities,
} from './MortgageWorkbench';

interface CalculationsPanelProps {
  ratios: MortgageRatios;
  stressRatios: MortgageStressRatios;
  loan: MortgageLoan;
  income: MortgageIncome;
  liabilities: MortgageLiabilities;
}

// OSFI B-20 limits (as percentages, e.g., 39 = 39%)
const OSFI_LIMITS = {
  gds: 39,
  tds: 44,
  ltv_insured: 95,
  ltv_conventional: 80,
  mqr_floor: 5.25,
  mqr_buffer: 2,
};

export default function CalculationsPanel({
  ratios,
  stressRatios,
  loan,
  income,
  liabilities,
}: CalculationsPanelProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const getRatioStatus = (value: number, limit: number): 'pass' | 'warning' | 'fail' => {
    if (value <= limit * 0.9) return 'pass';
    if (value <= limit) return 'warning';
    return 'fail';
  };

  const getStatusColor = (status: 'pass' | 'warning' | 'fail') => {
    switch (status) {
      case 'pass':
        return 'text-green-600';
      case 'warning':
        return 'text-amber-600';
      case 'fail':
        return 'text-red-600';
    }
  };

  const getStatusBg = (status: 'pass' | 'warning' | 'fail') => {
    switch (status) {
      case 'pass':
        return 'bg-green-50 border-green-200';
      case 'warning':
        return 'bg-amber-50 border-amber-200';
      case 'fail':
        return 'bg-red-50 border-red-200';
    }
  };

  // Get the interest rate (prefer contract_rate, fall back to rate)
  const interestRate = loan.contract_rate || loan.rate || 5.25;

  // Calculate monthly payment (simplified)
  const monthlyRate = interestRate / 100 / 12;
  const numPayments = loan.amortization_years * 12;
  const monthlyPayment = loan.amount * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / (Math.pow(1 + monthlyRate, numPayments) - 1);

  // Stress test rate (qualifying rate from API or calculate)
  const stressRate = loan.qualifying_rate || Math.max(interestRate + OSFI_LIMITS.mqr_buffer, OSFI_LIMITS.mqr_floor);
  const stressMonthlyRate = stressRate / 100 / 12;
  const stressPayment = loan.amount * (stressMonthlyRate * Math.pow(1 + stressMonthlyRate, numPayments)) / (Math.pow(1 + stressMonthlyRate, numPayments) - 1);

  const gdsStatus = getRatioStatus(stressRatios.gds, OSFI_LIMITS.gds);
  const tdsStatus = getRatioStatus(stressRatios.tds, OSFI_LIMITS.tds);
  const ltvStatus = getRatioStatus(ratios.ltv, ratios.ltv > 80 ? OSFI_LIMITS.ltv_insured : OSFI_LIMITS.ltv_conventional);

  return (
    <div className="space-y-6">
      {/* Ratio Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <RatioCard
          label="GDS (Stress)"
          value={stressRatios.gds}
          limit={OSFI_LIMITS.gds}
          status={gdsStatus}
          description="Gross Debt Service"
        />
        <RatioCard
          label="TDS (Stress)"
          value={stressRatios.tds}
          limit={OSFI_LIMITS.tds}
          status={tdsStatus}
          description="Total Debt Service"
        />
        <RatioCard
          label="LTV"
          value={ratios.ltv}
          limit={ratios.ltv > 0.8 ? OSFI_LIMITS.ltv_insured : OSFI_LIMITS.ltv_conventional}
          status={ltvStatus}
          description="Loan-to-Value"
        />
      </div>

      {/* Stress Test Section */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-emerald-600" />
          <h3 className="font-medium text-slate-900">OSFI B-20 Stress Test</h3>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-slate-700 mb-3">Contract Rate</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Interest Rate</span>
                  <span className="font-medium">{interestRate}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Monthly Payment</span>
                  <span className="font-medium">{formatCurrency(monthlyPayment)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">GDS Ratio</span>
                  <span className="font-medium">{formatPercent(ratios.gds)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">TDS Ratio</span>
                  <span className="font-medium">{formatPercent(ratios.tds)}</span>
                </div>
              </div>
            </div>
            <div className="border-l border-slate-200 pl-6">
              <h4 className="text-sm font-medium text-slate-700 mb-3">
                Qualifying Rate (MQR)
                <span className="ml-2 text-xs font-normal text-slate-500">
                  max(contract + 2%, 5.25%)
                </span>
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Stress Rate</span>
                  <span className="font-medium">{stressRate.toFixed(2)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Monthly Payment</span>
                  <span className="font-medium">{formatCurrency(stressPayment)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">GDS Ratio</span>
                  <span className={`font-medium ${getStatusColor(gdsStatus)}`}>
                    {formatPercent(stressRatios.gds)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">TDS Ratio</span>
                  <span className={`font-medium ${getStatusColor(tdsStatus)}`}>
                    {formatPercent(stressRatios.tds)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* GDS Calculation Breakdown */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center gap-2">
          <Calculator className="w-5 h-5 text-emerald-600" />
          <h3 className="font-medium text-slate-900">GDS Calculation Breakdown</h3>
        </div>
        <div className="p-4">
          <div className="space-y-3">
            <CalculationRow
              label="Monthly Mortgage Payment (P+I)"
              value={formatCurrency(stressPayment)}
              source="Calculated at MQR"
            />
            <CalculationRow
              label="Property Taxes (monthly)"
              value={formatCurrency(liabilities.property_taxes_monthly)}
              source="Municipal Estimate"
            />
            <CalculationRow
              label="Heating (monthly)"
              value={formatCurrency(liabilities.heating_monthly)}
              source="Utility Estimate"
            />
            {liabilities.condo_fees_monthly && liabilities.condo_fees_monthly > 0 && (
              <CalculationRow
                label="Condo Fees (50%)"
                value={formatCurrency(liabilities.condo_fees_monthly * 0.5)}
                source="Status Certificate"
              />
            )}
            <div className="border-t border-slate-200 pt-3 mt-3">
              <CalculationRow
                label="Total Housing Costs"
                value={formatCurrency(
                  stressPayment +
                  liabilities.property_taxes_monthly +
                  liabilities.heating_monthly +
                  (liabilities.condo_fees_monthly || 0) * 0.5
                )}
                bold
              />
            </div>
            <CalculationRow
              label="Gross Monthly Income"
              value={formatCurrency(income.total_annual_income / 12)}
              source="T4/Paystub"
            />
            <div className="border-t border-slate-200 pt-3 mt-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-slate-900">GDS Ratio</span>
                <div className="flex items-center gap-2">
                  <span className={`text-lg font-bold ${getStatusColor(gdsStatus)}`}>
                    {formatPercent(stressRatios.gds)}
                  </span>
                  <span className="text-sm text-slate-500">/ {formatPercent(OSFI_LIMITS.gds)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* TDS Calculation */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center gap-2">
          <Calculator className="w-5 h-5 text-emerald-600" />
          <h3 className="font-medium text-slate-900">TDS Calculation</h3>
        </div>
        <div className="p-4">
          <div className="space-y-3">
            <CalculationRow
              label="Housing Costs (from GDS)"
              value={formatCurrency(
                stressPayment +
                liabilities.property_taxes_monthly +
                liabilities.heating_monthly +
                (liabilities.condo_fees_monthly || 0) * 0.5
              )}
            />
            <CalculationRow
              label="Other Debt Payments"
              value={formatCurrency(liabilities.other_debts_monthly || 0)}
              source="Credit Bureau"
            />
            <div className="border-t border-slate-200 pt-3 mt-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-slate-900">TDS Ratio</span>
                <div className="flex items-center gap-2">
                  <span className={`text-lg font-bold ${getStatusColor(tdsStatus)}`}>
                    {formatPercent(stressRatios.tds)}
                  </span>
                  <span className="text-sm text-slate-500">/ {formatPercent(OSFI_LIMITS.tds)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper Components
function RatioCard({
  label,
  value,
  limit,
  status,
  description,
}: {
  label: string;
  value: number;
  limit: number;
  status: 'pass' | 'warning' | 'fail';
  description: string;
}) {
  // Values are already percentages (e.g., 26.36 means 26.36%)
  const formatPercent = (v: number) => `${v.toFixed(1)}%`;

  const getStatusIcon = () => {
    switch (status) {
      case 'pass':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      case 'fail':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
    }
  };

  const getStatusBg = () => {
    switch (status) {
      case 'pass':
        return 'bg-green-50 border-green-200';
      case 'warning':
        return 'bg-amber-50 border-amber-200';
      case 'fail':
        return 'bg-red-50 border-red-200';
    }
  };

  const getBarColor = () => {
    switch (status) {
      case 'pass':
        return 'bg-green-500';
      case 'warning':
        return 'bg-amber-500';
      case 'fail':
        return 'bg-red-500';
    }
  };

  const percentage = Math.min((value / limit) * 100, 100);

  return (
    <div className={`rounded-lg border p-4 ${getStatusBg()}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-slate-700">{label}</span>
        {getStatusIcon()}
      </div>
      <div className="text-2xl font-bold text-slate-900 mb-1">
        {formatPercent(value)}
      </div>
      <div className="text-xs text-slate-500 mb-3">
        Limit: {formatPercent(limit)}
      </div>
      <div className="w-full bg-slate-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all ${getBarColor()}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="text-xs text-slate-500 mt-2">{description}</div>
    </div>
  );
}

function CalculationRow({
  label,
  value,
  source,
  bold = false,
}: {
  label: string;
  value: string;
  source?: string;
  bold?: boolean;
}) {
  return (
    <div className="flex justify-between items-center">
      <div className="flex items-center gap-2">
        <span className={`text-sm ${bold ? 'font-medium text-slate-900' : 'text-slate-600'}`}>
          {label}
        </span>
        {source && (
          <span className="text-xs px-2 py-0.5 bg-slate-100 text-slate-500 rounded-full">
            {source}
          </span>
        )}
      </div>
      <span className={`text-sm ${bold ? 'font-medium text-slate-900' : 'text-slate-700'}`}>
        {value}
      </span>
    </div>
  );
}
