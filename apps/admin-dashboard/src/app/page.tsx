import * as React from 'react';
import type { CSSProperties } from 'react';

type DryRunSignal = {
  id: number;
  account_id: number;
  worker_id: number | null;
  symbol: string;
  timeframe: string;
  timeframes_json: string[] | null;
  direction: string;
  trend_bias: string | null;
  rr_estimate: string | null;
  status: string;
  rejection_reason: string | null;
  created_at: string;
};

export const dynamic = 'force-dynamic';

const panelStyle: CSSProperties = {
  background: '#111827',
  border: '1px solid #1f2937',
  borderRadius: 8,
  padding: 20,
};

const mutedStyle: CSSProperties = {
  color: '#9ca3af',
};

async function getDryRunSignals(): Promise<DryRunSignal[]> {
  const apiBaseUrl = process.env.API_BASE_URL ?? 'http://localhost:8000';
  const adminToken = process.env.ADMIN_API_TOKEN;

  if (!adminToken) {
    return [];
  }

  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/signals/dry-run`, {
      headers: {
        Authorization: `Bearer ${adminToken}`,
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      return [];
    }

    return response.json();
  } catch {
    return [];
  }
}

export default async function DashboardPage() {
  const signals = await getDryRunSignals();
  const acceptedCount = signals.filter((signal) => signal.status === 'accepted').length;
  const rejectedCount = signals.filter((signal) => signal.status === 'rejected').length;

  const items = [
    { label: 'Dry-run Signals', value: String(signals.length), note: 'Recent strategy decisions' },
    { label: 'Accepted', value: String(acceptedCount), note: 'Candidates generated' },
    { label: 'Rejected', value: String(rejectedCount), note: 'Blocked by rules' },
    { label: 'Execution', value: 'Off', note: 'Dry-run only' },
  ];

  return (
    <main style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 32 }}>Auto Gold Bot Admin</h1>
        <p style={mutedStyle}>Dry-run strategy monitoring for XAUUSD worker outcomes.</p>
      </div>

      <section
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 16,
          marginBottom: 24,
        }}
      >
        {items.map((item) => (
          <div key={item.label} style={panelStyle}>
            <div style={{ ...mutedStyle, marginBottom: 10 }}>{item.label}</div>
            <div style={{ fontSize: 28, fontWeight: 700 }}>{item.value}</div>
            <div style={{ ...mutedStyle, marginTop: 10, lineHeight: 1.5 }}>{item.note}</div>
          </div>
        ))}
      </section>

      <section style={panelStyle}>
        <h2 style={{ marginTop: 0 }}>Dry-run Outcomes</h2>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 860 }}>
            <thead>
              <tr style={{ color: '#9ca3af', textAlign: 'left' }}>
                <th style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>ID</th>
                <th style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>Account</th>
                <th style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>Worker</th>
                <th style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>Symbol</th>
                <th style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>Frames</th>
                <th style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>Direction</th>
                <th style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>Bias</th>
                <th style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>RR</th>
                <th style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>Status</th>
                <th style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>Reason</th>
              </tr>
            </thead>
            <tbody>
              {signals.slice(0, 25).map((signal) => (
                <tr key={signal.id}>
                  <td style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>{signal.id}</td>
                  <td style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>{signal.account_id}</td>
                  <td style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>{signal.worker_id ?? '-'}</td>
                  <td style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>{signal.symbol}</td>
                  <td style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>
                    {(signal.timeframes_json ?? [signal.timeframe]).join(' / ')}
                  </td>
                  <td style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>{signal.direction}</td>
                  <td style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>{signal.trend_bias ?? '-'}</td>
                  <td style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>{signal.rr_estimate ?? '-'}</td>
                  <td style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>{signal.status}</td>
                  <td style={{ padding: '10px 8px', borderBottom: '1px solid #1f2937' }}>{signal.rejection_reason ?? '-'}</td>
                </tr>
              ))}
              {signals.length === 0 && (
                <tr>
                  <td colSpan={10} style={{ ...mutedStyle, padding: 16, textAlign: 'center' }}>
                    No dry-run outcomes available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
