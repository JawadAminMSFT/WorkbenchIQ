/**
 * Customer 360 TypeScript type definitions.
 * Matches the backend data models in app/customer360.py.
 */

export interface CustomerProfile {
  id: string;
  name: string;
  date_of_birth: string;
  email: string;
  phone: string;
  address: string;
  customer_since: string;
  risk_tier: 'low' | 'medium' | 'high';
  tags: string[];
  notes: string;
}

export interface CustomerJourneyEvent {
  date: string;
  persona: string;
  application_id: string;
  event_type: string;
  title: string;
  summary: string;
  status: string;
  risk_level: string | null;
  key_metrics: Record<string, string>;
}

export interface PersonaSummary {
  persona: string;
  persona_label: string;
  application_count: number;
  latest_status: string;
  risk_level: string | null;
  key_metrics: Record<string, string>;
  applications: CustomerJourneyEvent[];
}

export interface RiskCorrelation {
  severity: 'info' | 'warning' | 'critical';
  title: string;
  description: string;
  personas_involved: string[];
}

export interface Customer360View {
  profile: CustomerProfile;
  journey_events: CustomerJourneyEvent[];
  persona_summaries: PersonaSummary[];
  risk_correlations: RiskCorrelation[];
  total_products: number;
  active_claims: number;
  overall_risk: string;
}
