import * as React from 'react';
import type { CSSProperties } from 'react';

const cardStyle: CSSProperties = {
  background: '#111827',
  border: '1px solid #1f2937',
  borderRadius: 16,
  padding: 20,
};

export default function DashboardPage() {
  const items = [
    { label: 'Clients', value: '0', note: 'Add client profiles and contact details' },
    { label: 'Accounts', value: '0', note: 'Attach MT5 monitor or execute accounts' },
    { label: 'Workers', value: '0', note: 'Per-account execution agents' },
    { label: 'Open Trades', value: '0', note: 'Live trade monitoring will appear here' },
  ];

  return (
    <main style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 32 }}>Auto Gold Bot Admin</h1>
        <p style={{ color: '#9ca3af' }}>
          Private admin-managed multi-account trading platform for XAUUSD strategy operations.
        </p>
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
          <div key={item.label} style={cardStyle}>
            <div style={{ color: '#9ca3af', marginBottom: 10 }}>{item.label}</div>
            <div style={{ fontSize: 28, fontWeight: 700 }}>{item.value}</div>
            <div style={{ color: '#9ca3af', marginTop: 10, lineHeight: 1.5 }}>{item.note}</div>
          </div>
        ))}
      </section>

      <section style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16 }}>
        <div style={cardStyle}>
          <h2 style={{ marginTop: 0 }}>MVP Modules</h2>
          <ul style={{ lineHeight: 1.8, paddingLeft: 18 }}>
            <li>Client and account management</li>
            <li>Bot configuration presets</li>
            <li>Signal and trade journal</li>
            <li>Worker heartbeat and status</li>
            <li>Emergency stop per account</li>
            <li>Read-only monitoring for investor access</li>
          </ul>
        </div>
        <div style={cardStyle}>
          <h2 style={{ marginTop: 0 }}>Next Actions</h2>
          <ol style={{ lineHeight: 1.8, paddingLeft: 18 }}>
            <li>Freeze strict strategy rules</li>
            <li>Add auth and permissions</li>
            <li>Connect real MT5 worker</li>
            <li>Add migrations and tests</li>
          </ol>
        </div>
      </section>
    </main>
  );
}
