'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Menu, X, ArrowUpRight, MessageSquare } from 'lucide-react';

const navItems = [
  { href: '#terminal',      label: 'Live Assistant' },
  { href: '#features',      label: 'Features' },
  { href: '#architecture',  label: 'How It Works' },
  { href: '#capabilities',  label: 'Banking Services' },
  { href: '#demo',          label: 'Test Scenarios' },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 15);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        transition: 'all 0.2s ease',
        background: scrolled ? 'rgba(255, 255, 255, 0.94)' : 'rgba(250, 250, 250, 0.8)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        borderBottom: scrolled ? '1px solid var(--border-hairline)' : '1px solid transparent',
      }}
    >
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '64px' }}>
        {/* Brand */}
        <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '10px', textDecoration: 'none' }}>
          <div
            style={{
              width: '30px',
              height: '30px',
              borderRadius: '8px',
              background: '#09090b',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '0.9rem',
              fontFamily: 'var(--font-heading)',
            }}
          >
            N
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
            <span style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
              NexaBank
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>
              AI Support
            </span>
          </div>
        </Link>

        {/* Nav Links */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '26px' }} className="desktop-menu">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              style={{
                fontSize: '0.88rem',
                fontWeight: 500,
                color: 'var(--text-body)',
                textDecoration: 'none',
                transition: 'color 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-main)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-body)')}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        {/* CTA */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }} className="desktop-actions">
          <a href="#terminal" className="btn-solid" style={{ padding: '8px 16px', fontSize: '0.84rem' }}>
            <MessageSquare size={14} />
            Try Live Chat
          </a>
        </div>

        {/* Mobile menu toggle */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          style={{
            display: 'none',
            background: 'none',
            border: 'none',
            color: 'var(--text-main)',
            cursor: 'pointer',
            padding: '6px',
          }}
          className="mobile-button"
          aria-label="Toggle Menu"
        >
          {mobileOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile nav dropdown */}
      {mobileOpen && (
        <div
          style={{
            background: '#ffffff',
            borderBottom: '1px solid var(--border-hairline)',
            padding: '16px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
          }}
        >
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              style={{
                fontSize: '0.92rem',
                fontWeight: 600,
                color: 'var(--text-main)',
                textDecoration: 'none',
                padding: '6px 0',
              }}
            >
              {item.label}
            </Link>
          ))}
          <a
            href="#terminal"
            onClick={() => setMobileOpen(false)}
            className="btn-solid"
            style={{ marginTop: '8px', textAlign: 'center' }}
          >
            Try Live Chat
          </a>
        </div>
      )}

      <style>{`
        @media (max-width: 768px) {
          .desktop-menu, .desktop-actions { display: none !important; }
          .mobile-button { display: block !important; }
        }
      `}</style>
    </header>
  );
}
