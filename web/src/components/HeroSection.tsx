'use client';

import { ArrowDown, MessageSquare, ShieldCheck, Zap, Clock } from 'lucide-react';
import LiveChatCopilot from './LiveChatCopilot';

export default function HeroSection() {
  return (
    <section
      id="hero"
      className="bg-subtle-grid"
      style={{
        paddingTop: '100px',
        paddingBottom: '60px',
        borderBottom: '1px solid var(--border-hairline)',
        position: 'relative',
      }}
    >
      <div className="container">
        {/* Top Product Headline */}
        <div style={{ textAlign: 'center', maxWidth: '800px', margin: '0 auto 36px auto' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <span className="tag-pill tag-accent" style={{ fontWeight: 600, fontSize: '0.78rem' }}>
              NexaBank AI Assistant
            </span>
            <span className="tag-pill tag-success" style={{ fontWeight: 600, fontSize: '0.78rem' }}>
              Live & Interactive
            </span>
          </div>

          <h1 className="title-hero" style={{ marginBottom: '18px' }}>
            Intelligent Customer Support for Modern Retail Banking
          </h1>

          <p style={{ fontSize: '1.1rem', color: 'var(--text-body)', lineHeight: 1.6, maxWidth: '640px', margin: '0 auto 28px auto' }}>
            Instant, automated assistance for account balances, card controls, transaction disputes, and bank policies — all in natural conversation.
          </p>

          {/* Key Value Highlights */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '12px',
              maxWidth: '780px',
              margin: '0 auto',
            }}
          >
            {[
              { label: 'Instant Resolution', desc: 'Real-time answers for accounts & cards' },
              { label: 'Card Security', desc: 'One-click block & replacement support' },
              { label: 'Context Aware', desc: 'Remembers details across conversation' },
              { label: 'Policy Expert', desc: 'UPI, NEFT & KYC guidance' },
            ].map((stat, i) => (
              <div
                key={i}
                style={{
                  padding: '12px 14px',
                  background: '#ffffff',
                  border: '1px solid var(--border-hairline)',
                  borderRadius: '8px',
                  textAlign: 'left',
                  boxShadow: 'var(--shadow-subtle)',
                }}
              >
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '2px' }}>
                  {stat.label}
                </div>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                  {stat.desc}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live Chat Copilot */}
        <div style={{ position: 'relative' }}>
          <LiveChatCopilot />
        </div>
      </div>

      <style>{`
        @media (max-width: 640px) {
          #hero div[style*="grid-template-columns: repeat(4, 1fr)"] {
            grid-template-columns: repeat(2, 1fr) !important;
          }
        }
      `}</style>
    </section>
  );
}
