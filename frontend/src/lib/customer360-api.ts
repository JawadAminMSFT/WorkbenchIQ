/**
 * API client for Customer 360 endpoints.
 */

import type { CustomerProfile, Customer360View } from './customer360-types';

/**
 * List all customer profiles.
 */
export async function listCustomers(): Promise<CustomerProfile[]> {
  const res = await fetch('/api/customers', { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch customers: ${res.status}`);
  }
  return res.json();
}

/**
 * Get full Customer 360 view for a specific customer.
 */
export async function getCustomer360(customerId: string): Promise<Customer360View> {
  const res = await fetch(`/api/customers/${encodeURIComponent(customerId)}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch customer 360: ${res.status}`);
  }
  return res.json();
}

/**
 * Seed sample customer 360 data (development/demo only).
 */
export async function seedCustomer360Data(): Promise<{ status: string; message: string }> {
  const res = await fetch('/api/customers/seed', { method: 'POST' });
  if (!res.ok) {
    throw new Error(`Failed to seed customer data: ${res.status}`);
  }
  return res.json();
}
