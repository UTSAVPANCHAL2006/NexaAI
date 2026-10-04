'use client';

import Link from 'next/link';

export default function Footer() {
  return (
    <footer style={{ background: '#ffffff', borderTop: '1px solid var(--border-hairline)', padding: '40px 0 32px 0' }}>
      <div className="container">
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '20px',
            marginBottom: '24px',
          }}
        >
          {/* Brand */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '7px',
                background: '#09090b',
                color: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                fontSize: '0.85rem',
                fontFamily: 'var(--font-heading)',
              }}
            >
              N
            </div>
            <span style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
              NexaBank
            </span>
          </div>

          {/* Quick Links */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexWrap: 'wrap' }}>
            <a
              href="#terminal"
              style={{
                fontSize: '0.85rem',
                color: 'var(--text-body)',
                textDecoration: 'none',
                transition: 'color 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-main)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-body)')}
            >
              Live Assistant
            </a>

            <a
              href="#features"
              style={{
                fontSize: '0.85rem',
                color: 'var(--text-body)',
                textDecoration: 'none',
                transition: 'color 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-main)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-body)')}
            >
              Features
            </a>

            <a
              href="#capabilities"
              style={{
                fontSize: '0.85rem',
                color: 'var(--text-body)',
                textDecoration: 'none',
                transition: 'color 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-main)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-body)')}
            >
              Banking Services
            </a>

            <a
              href="#demo"
              style={{
                fontSize: '0.85rem',
                color: 'var(--text-body)',
                textDecoration: 'none',
                transition: 'color 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-main)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-body)')}
            >
              Test Scenarios
            </a>
          </div>
        </div>

        {/* Bottom Line */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
            paddingTop: '20px',
            borderTop: '1px solid var(--border-hairline)',
            fontSize: '0.82rem',
            color: 'var(--text-muted)',
          }}
        >
          <div>
            © 2026 NexaBank. All rights reserved.
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className="status-pip status-pip-live" />
            <span>Systems Operational</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
