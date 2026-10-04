'use client';

import { useState } from 'react';
import { ChevronRight, ShieldCheck, CheckCircle2, ArrowRight } from 'lucide-react';

const workflowSteps = [
  {
    step: 'Step 1',
    title: 'Safety & Security Verification',
    summary: 'Instant protection against unauthorized prompts and malicious inputs.',
    details: 'Before any processing begins, security filters ensure your query is safe, relevant to banking, and free from malicious injection attempts.',
    keyBenefit: 'Protects customer privacy and blocks harmful requests instantly.',
  },
  {
    step: 'Step 2',
    title: 'Intent & Request Classification',
    summary: 'Identifies whether you need account data, card actions, or policy information.',
    details: 'The assistant understands the exact purpose of your message — whether checking a balance, reporting a stolen card, investigating a failed transaction, or asking about bank policies.',
    keyBenefit: 'Routes your inquiry directly to the right specialized banking service.',
  },
  {
    step: 'Step 3',
    title: 'Entity & Context Resolution',
    summary: 'Identifies account numbers and remembers context across turns.',
    details: 'Extracts relevant identifiers (like account IDs, transaction numbers, or card endings) and links them with your ongoing conversation so you can ask natural follow-up questions.',
    keyBenefit: 'You can say "What about its recent debits?" without repeating your account number.',
  },
  {
    step: 'Step 4',
    title: 'Banking System & Policy Lookup',
    summary: 'Retrieves live account data or verified bank guidelines.',
    details: 'Securely reads real-time account balances, executes card status changes, or searches verified banking knowledge for NPCI/RBI policy guidelines.',
    keyBenefit: 'Delivers factual, verified answers from official banking data sources.',
  },
  {
    step: 'Step 5',
    title: 'Grounded Answer & State Save',
    summary: 'Formats clean, clear responses with sensitive data protection.',
    details: 'Formats the final answer clearly with masked sensitive digits (e.g. card ****4521) and saves conversation history so you can continue the chat anytime.',
    keyBenefit: 'Clear, concise answers with zero exposure of sensitive PINs or full numbers.',
  },
];

export default function ArchitectureSection() {
  const [activeStep, setActiveStep] = useState(0);
  const current = workflowSteps[activeStep];

  return (
    <section id="architecture" className="section" style={{ borderBottom: '1px solid var(--border-hairline)', background: '#ffffff' }}>
      <div className="container">
        <div style={{ marginBottom: '40px' }}>
          <span className="tag-pill tag-default" style={{ marginBottom: '12px' }}>
            Workflow
          </span>
          <h2 className="title-section" style={{ marginBottom: '12px' }}>
            How NexaBank Handles Your Requests
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '1rem', maxWidth: '600px' }}>
            Every question goes through a reliable 5-step process designed for safety, accuracy, and continuous memory.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1.2fr',
            gap: '32px',
            alignItems: 'start',
          }}
        >
          {/* Step Selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {workflowSteps.map((item, idx) => {
              const isActive = activeStep === idx;
              return (
                <button
                  key={item.step}
                  onClick={() => setActiveStep(idx)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '14px 18px',
                    borderRadius: '8px',
                    background: isActive ? 'var(--bg-dark)' : 'var(--bg-subtle)',
                    color: isActive ? '#ffffff' : 'var(--text-main)',
                    border: '1px solid',
                    borderColor: isActive ? 'var(--bg-dark)' : 'var(--border-hairline)',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all var(--transition-fast)',
                  }}
                >
                  <div>
                    <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: isActive ? '#a1a1aa' : 'var(--text-muted)', fontWeight: 600 }}>
                      {item.step}
                    </div>
                    <div style={{ fontSize: '0.92rem', fontWeight: 700, marginTop: '2px' }}>
                      {item.title}
                    </div>
                  </div>
                  <ChevronRight size={16} color={isActive ? '#ffffff' : 'var(--text-dim)'} />
                </button>
              );
            })}
          </div>

          {/* Details Card */}
          <div
            className="surface-card"
            style={{
              padding: '32px',
              background: '#fafafa',
              border: '1px solid var(--border-hairline)',
            }}
          >
            <span className="tag-pill tag-accent" style={{ marginBottom: '14px', display: 'inline-flex' }}>
              {current.step} Details
            </span>

            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '12px' }}>
              {current.title}
            </h3>

            <p style={{ fontSize: '0.94rem', color: 'var(--text-body)', lineHeight: 1.65, marginBottom: '20px' }}>
              {current.details}
            </p>

            <div
              style={{
                padding: '14px 16px',
                background: '#ffffff',
                border: '1px solid var(--border-hairline)',
                borderRadius: '8px',
                display: 'flex',
                gap: '10px',
                alignItems: 'flex-start',
              }}
            >
              <CheckCircle2 size={18} color="var(--brand-success)" style={{ marginTop: '2px', flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '2px' }}>
                  Customer Benefit
                </div>
                <div style={{ fontSize: '0.84rem', color: 'var(--text-body)', lineHeight: 1.5 }}>
                  {current.keyBenefit}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 860px) {
          #architecture div[style*="grid-template-columns: 1fr 1.2fr"] {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </section>
  );
}
