'use client';

import { useState } from 'react';
import {
  Wallet, CreditCard, Receipt, FileCheck, LifeBuoy, HelpCircle,
  ArrowRight, MessageSquare
} from 'lucide-react';

const domainServices = [
  {
    id: 'account',
    name: 'Account Services',
    icon: Wallet,
    tagline: 'Balance checks, transaction history & spending summaries',
    capabilities: [
      'Real-time available balance and hold amount',
      'Recent deposits, withdrawals and UPI debits',
      'Monthly spending breakdown by category (dining, shopping, bills)',
    ],
    sampleQuestion: 'What is the balance for account ACC-1007?',
    sampleAnswer: 'Account ACC-1007 — Savings\nAvailable Balance: ₹1,24,580.00\nHold Amount: ₹0.00\nLast Transaction: Sep 28, 2026',
  },
  {
    id: 'card',
    name: 'Card Management',
    icon: CreditCard,
    tagline: 'Card controls, emergency freezing & re-issuance',
    capabilities: [
      'Instant card status lookup (Active, Blocked, Expired)',
      'Emergency card lock for lost or stolen cards',
      'Automated replacement card requests dispatched to your address',
    ],
    sampleQuestion: 'Block my card ending in 4521 because I lost it',
    sampleAnswer: 'Card ending in 4521 has been successfully BLOCKED (Lost/Stolen).\nCase CASE-3088 has been opened. A replacement card will be dispatched within 5-7 business days.',
  },
  {
    id: 'transaction',
    name: 'Transaction Support',
    icon: Receipt,
    tagline: 'Payment diagnostics, pending transfers & status checks',
    capabilities: [
      'Root-cause explanations for failed UPI or card transactions',
      'Real-time status tracking for pending transfers',
      'Detailed transaction lookup by ID (amount, timestamp, merchant)',
    ],
    sampleQuestion: 'Why did transaction TXN-9025 fail?',
    sampleAnswer: 'Transaction TXN-9025 failed due to insufficient account balance at the time of processing.\nAvailable Balance: ₹200.00 | Attempted Debit: ₹2,400.00.',
  },
  {
    id: 'kyc',
    name: 'KYC & Verification',
    icon: FileCheck,
    tagline: 'Account verification, document status & upgrade guidance',
    capabilities: [
      'KYC status verification (Full KYC vs Partial KYC)',
      'Document checklist (PAN, Aadhaar, Passport)',
      'Next review dates and upgrade requirements',
    ],
    sampleQuestion: 'Check KYC status and missing documents for user_7',
    sampleAnswer: 'Customer user_7 (Rajesh Kumar) Status: FULL KYC\nAadhaar: Verified | PAN: Verified\nAll documents are up-to-date. Next scheduled review: March 2027.',
  },
  {
    id: 'case',
    name: 'Disputes & Tickets',
    icon: LifeBuoy,
    tagline: 'Automated case creation & resolution tracking',
    capabilities: [
      'Official dispute filing for unauthorized charges',
      'Real-time tracking of active support tickets',
      'Expected resolution dates and officer notes',
    ],
    sampleQuestion: 'What is the status of dispute CASE-3001?',
    sampleAnswer: 'Dispute CASE-3001 (Unauthorized Transaction):\nStatus: IN REVIEW | Opened: Sep 22, 2026\nEstimated Resolution Date: Oct 6, 2026.',
  },
  {
    id: 'policy',
    name: 'Banking Policies & FAQs',
    icon: HelpCircle,
    tagline: 'Verified regulatory knowledge, UPI rules & settlement cutoffs',
    capabilities: [
      'NPCI UPI auto-reversal and compensation timelines',
      'NEFT/RTGS batch timings and cutoff rules',
      'Savings interest calculation and account maintenance rules',
    ],
    sampleQuestion: 'What is the refund timeline if a UPI payment failed but money was deducted?',
    sampleAnswer: 'Under NPCI regulations: If money is debited from your account but the merchant does not receive credit, the amount will be auto-reversed to your account within T+5 working days. If delayed beyond this timeline, banks provide compensation of ₹100 per day.',
  },
];

export default function CapabilitiesSection() {
  const [selectedIdx, setSelectedIdx] = useState(0);
  const activeService = domainServices[selectedIdx];

  return (
    <section id="capabilities" className="section" style={{ borderBottom: '1px solid var(--border-hairline)', background: '#fafafa' }}>
      <div className="container">
        <div style={{ marginBottom: '36px' }}>
          <span className="tag-pill tag-default" style={{ marginBottom: '12px' }}>
            Banking Services
          </span>
          <h2 className="title-section" style={{ marginBottom: '12px' }}>
            Supported Everyday Inquiries
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '1rem', maxWidth: '600px' }}>
            Select a banking domain below to see what the assistant can handle and view real example responses.
          </p>
        </div>

        {/* Horizontal Service Buttons */}
        <div
          style={{
            display: 'flex',
            gap: '8px',
            overflowX: 'auto',
            paddingBottom: '10px',
            marginBottom: '24px',
          }}
        >
          {domainServices.map((service, idx) => {
            const Icon = service.icon;
            const isSelected = selectedIdx === idx;
            return (
              <button
                key={service.id}
                onClick={() => setSelectedIdx(idx)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 16px',
                  borderRadius: '8px',
                  background: isSelected ? 'var(--bg-dark)' : '#ffffff',
                  color: isSelected ? '#ffffff' : 'var(--text-main)',
                  border: '1px solid',
                  borderColor: isSelected ? 'var(--bg-dark)' : 'var(--border-hairline)',
                  fontSize: '0.86rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  boxShadow: isSelected ? 'var(--shadow-subtle)' : 'none',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <Icon size={16} />
                <span>{service.name}</span>
              </button>
            );
          })}
        </div>

        {/* Clean Responsive Details Card */}
        <div
          className="surface-card"
          style={{
            padding: '36px',
            background: '#ffffff',
            display: 'grid',
            gridTemplateColumns: '1.1fr 1fr',
            gap: '40px',
            alignItems: 'start',
          }}
        >
          {/* Left Column: Capabilities List */}
          <div>
            <div style={{ fontSize: '0.78rem', color: 'var(--brand-accent)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '6px' }}>
              {activeService.name}
            </div>

            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px' }}>
              {activeService.tagline}
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', margin: '20px 0 28px 0' }}>
              {activeService.capabilities.map((item, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '0.9rem', color: 'var(--text-body)' }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--brand-accent)', marginTop: '8px', flexShrink: 0 }} />
                  <span>{item}</span>
                </div>
              ))}
            </div>

            <a
              href="#terminal"
              className="btn-solid"
              style={{ padding: '9px 18px', fontSize: '0.84rem' }}
            >
              <MessageSquare size={14} />
              Try this in Live Assistant
            </a>
          </div>

          {/* Right Column: Q&A Preview */}
          <div
            style={{
              background: '#f8fafc',
              border: '1px solid var(--border-hairline)',
              borderRadius: '10px',
              padding: '22px',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
              Sample Customer Question
            </div>
            <div
              style={{
                padding: '12px 14px',
                background: '#ffffff',
                border: '1px solid var(--border-hairline)',
                borderRadius: '6px',
                fontSize: '0.88rem',
                fontWeight: 600,
                color: 'var(--text-main)',
                marginBottom: '18px',
              }}
            >
              &quot;{activeService.sampleQuestion}&quot;
            </div>

            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
              Assistant Response
            </div>
            <div
              style={{
                padding: '14px 16px',
                background: '#ffffff',
                border: '1px solid var(--border-hairline)',
                borderRadius: '6px',
                fontSize: '0.85rem',
                lineHeight: 1.65,
                color: 'var(--text-main)',
                whiteSpace: 'pre-line',
                fontFamily: activeService.sampleAnswer.includes('Available Balance') ? 'var(--font-mono)' : 'var(--font-sans)',
              }}
            >
              {activeService.sampleAnswer}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 860px) {
          #capabilities div[style*="grid-template-columns: 1.1fr 1fr"] {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </section>
  );
}
