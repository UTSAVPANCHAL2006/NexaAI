'use client';

import { ArrowUpRight, MessageSquare, ShieldCheck, Check, UserCheck, CreditCard, AlertTriangle, Layers } from 'lucide-react';

const customerScenarios = [
  {
    id: 'ACC-1007',
    tag: 'Account Balance',
    name: 'Active Savings Account',
    detail: 'Has ₹1,24,580 balance and is linked to Platinum Visa card ending 4521.',
    suggestedPrompt: 'What is the balance for account ACC-1007 and what card is linked?',
  },
  {
    id: 'TXN-9025',
    tag: 'Failed Transaction',
    name: 'Declined UPI Transfer',
    detail: 'Attempted ₹2,400 transfer with ₹200 available balance.',
    suggestedPrompt: 'Why did transaction TXN-9025 fail?',
  },
  {
    id: 'CASE-3001',
    tag: 'Support Dispute',
    name: 'Dispute in Review',
    detail: 'Open claim regarding unauthorized charge. Target resolution Oct 6.',
    suggestedPrompt: 'Check status of dispute case CASE-3001',
  },
  {
    id: 'user_7',
    tag: 'Customer Profile',
    name: 'Verified Customer (Rajesh)',
    detail: 'Full KYC completed with verified PAN and Aadhaar records.',
    suggestedPrompt: 'Check KYC status and verified documents for user_7',
  },
  {
    id: 'ACC-1015',
    tag: 'Action Required',
    name: 'Partial KYC Account',
    detail: 'Requires pending PAN submission within 30 days to avoid restrictions.',
    suggestedPrompt: 'What is the KYC status and missing documents for ACC-1015?',
  },
];

export default function DemoSection() {
  return (
    <section id="demo" className="section" style={{ borderBottom: '1px solid var(--border-hairline)', background: '#ffffff' }}>
      <div className="container">
        <div style={{ marginBottom: '36px' }}>
          <span className="tag-pill tag-default" style={{ marginBottom: '12px' }}>
            Interactive Testing
          </span>
          <h2 className="title-section" style={{ marginBottom: '12px' }}>
            Sample Customer Profiles to Test
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '1rem', maxWidth: '640px' }}>
            Test the assistant instantly using pre-loaded test profiles. You can query these directly in the live assistant above.
          </p>
        </div>

        {/* Profiles Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '16px',
            marginBottom: '40px',
          }}
        >
          {customerScenarios.map((item) => (
            <div
              key={item.id}
              className="surface-card"
              style={{
                padding: '20px',
                background: '#fafafa',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <code style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--brand-accent)', background: '#ffffff' }}>
                    {item.id}
                  </code>
                  <span className="tag-pill tag-default" style={{ fontSize: '0.68rem' }}>
                    {item.tag}
                  </span>
                </div>

                <div style={{ fontSize: '0.94rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                  {item.name}
                </div>

                <p style={{ fontSize: '0.82rem', color: 'var(--text-body)', lineHeight: 1.5, marginBottom: '14px' }}>
                  {item.detail}
                </p>
              </div>

              <div style={{ paddingTop: '12px', borderTop: '1px solid var(--border-hairline)' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px', fontWeight: 600 }}>
                  Suggested Query:
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-main)', fontStyle: 'italic', marginBottom: '12px' }}>
                  &quot;{item.suggestedPrompt}&quot;
                </div>
                <a
                  href="#terminal"
                  className="btn-outline"
                  style={{ width: '100%', padding: '6px 12px', fontSize: '0.78rem', justifyContent: 'center' }}
                >
                  Ask This in Chat ↑
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
