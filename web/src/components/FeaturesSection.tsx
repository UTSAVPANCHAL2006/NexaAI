'use client';

import {
  Wallet, CreditCard, AlertCircle, FileCheck, LifeBuoy,
  HelpCircle
} from 'lucide-react';

const serviceFeatures = [
  {
    icon: Wallet,
    title: 'Account Inquiries & Balances',
    description: 'Instant access to current savings balances, recent debits & credits, and monthly categorized spending summaries.',
    badge: 'Accounts',
  },
  {
    icon: CreditCard,
    title: 'Card Security & Emergency Freeze',
    description: 'Instantly block lost or stolen cards, check card limits and expiry dates, and order replacement cards.',
    badge: 'Cards',
  },
  {
    icon: AlertCircle,
    title: 'Transaction Diagnostics',
    description: 'Understand exactly why a payment failed (insufficient balance, network timeout) and track pending transfers in real time.',
    badge: 'Transactions',
  },
  {
    icon: FileCheck,
    title: 'KYC & Document Verification',
    description: 'Check customer KYC completion status, identify missing documents (PAN/Aadhaar), and receive step-by-step upgrade instructions.',
    badge: 'KYC',
  },
  {
    icon: LifeBuoy,
    title: 'Dispute & Case Resolution',
    description: 'Open official dispute cases for unauthorized charges or failed UPI debits with live tracking and resolution estimates.',
    badge: 'Disputes',
  },
  {
    icon: HelpCircle,
    title: 'Bank Policies & FAQ Knowledge',
    description: 'Clear answers on RBI/NPCI UPI refund timelines, NEFT/RTGS settlement cutoffs, and regulatory requirements.',
    badge: 'Policies',
  },
];

export default function FeaturesSection() {
  return (
    <section id="features" className="section" style={{ borderBottom: '1px solid var(--border-hairline)', background: '#fafafa' }}>
      <div className="container">
        <div style={{ marginBottom: '40px' }}>
          <span className="tag-pill tag-default" style={{ marginBottom: '12px' }}>
            Banking Capabilities
          </span>
          <h2 className="title-section" style={{ marginBottom: '12px' }}>
            What NexaBank AI Can Do For You
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '1rem', maxWidth: '600px' }}>
            A comprehensive customer support assistant capable of answering everyday banking questions and executing account actions.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '20px',
          }}
        >
          {serviceFeatures.map((f, i) => {
            const Icon = f.icon;
            return (
              <div
                key={i}
                className="surface-card surface-card-hover"
                style={{
                  padding: '24px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  background: '#ffffff',
                }}
              >
                <div>
                  <div
                    style={{
                      width: '38px',
                      height: '38px',
                      borderRadius: '8px',
                      background: 'var(--bg-subtle)',
                      border: '1px solid var(--border-hairline)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginBottom: '16px',
                      color: 'var(--text-main)',
                    }}
                  >
                    <Icon size={19} strokeWidth={2} />
                  </div>

                  <h3 style={{ fontSize: '1.02rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px' }}>
                    {f.title}
                  </h3>

                  <p style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.6, marginBottom: '20px' }}>
                    {f.description}
                  </p>
                </div>

                <div>
                  <span className="tag-pill tag-default" style={{ fontSize: '0.7rem' }}>
                    {f.badge}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
