'use client';

import { useState } from 'react';
import { Copy, Check, Terminal, Server, Shield, ExternalLink } from 'lucide-react';

const codeExamples = {
  curl: `curl -N -X POST http://127.0.0.1:8000/chat \\
  -H "Content-Type: application/json" \\
  -H "X-Thread-ID: demo-session-1" \\
  -d '{
    "ticket": "What is the balance for account ACC-1007?",
    "thread_id": "demo-session-1"
  }'`,
  python: `import httpx

with httpx.stream(
    "POST",
    "http://127.0.0.1:8000/chat",
    json={"ticket": "Balance for ACC-1007", "thread_id": "demo-1"},
    timeout=30.0
) as r:
    for chunk in r.iter_text():
        print(chunk, end="", flush=True)`,
  typescript: `const res = await fetch('http://127.0.0.1:8000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-Thread-ID': 'demo-1' },
  body: JSON.stringify({ ticket: 'Balance for ACC-1007', thread_id: 'demo-1' })
});

const reader = res.body?.getReader();
const decoder = new TextDecoder();
while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  process.stdout.write(decoder.decode(value));
}`,
};

export default function APISection() {
  const [lang, setLang] = useState<'curl' | 'python' | 'typescript'>('curl');
  const [copied, setCopied] = useState(false);

  const copyCode = () => {
    navigator.clipboard.writeText(codeExamples[lang]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="api" className="section" style={{ borderBottom: '1px solid var(--border-hairline)', background: '#fafafa' }}>
      <div className="container">
        <div style={{ marginBottom: '48px' }}>
          <span className="tag-pill tag-default" style={{ marginBottom: '12px' }}>
            API Reference
          </span>
          <h2 className="title-section" style={{ marginBottom: '12px' }}>
            REST & Token Streaming Engine
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '1rem', maxWidth: '600px' }}>
            FastAPI server with chunked HTTP streaming, Redis rate-limiting (5 req/60s), and thread state headers.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1.2fr 0.8fr',
            gap: '32px',
            alignItems: 'start',
          }}
        >
          {/* Code Window */}
          <div
            className="surface-card"
            style={{
              background: '#09090b',
              border: '1px solid #27272a',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 16px',
                borderBottom: '1px solid #27272a',
                background: '#18181b',
              }}
            >
              <div style={{ display: 'flex', gap: '6px' }}>
                <button
                  onClick={() => setLang('curl')}
                  style={{
                    background: lang === 'curl' ? '#27272a' : 'transparent',
                    color: lang === 'curl' ? '#ffffff' : '#a1a1aa',
                    border: 'none', padding: '4px 10px', borderRadius: '4px',
                    fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer',
                  }}
                >
                  cURL
                </button>
                <button
                  onClick={() => setLang('python')}
                  style={{
                    background: lang === 'python' ? '#27272a' : 'transparent',
                    color: lang === 'python' ? '#ffffff' : '#a1a1aa',
                    border: 'none', padding: '4px 10px', borderRadius: '4px',
                    fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer',
                  }}
                >
                  Python
                </button>
                <button
                  onClick={() => setLang('typescript')}
                  style={{
                    background: lang === 'typescript' ? '#27272a' : 'transparent',
                    color: lang === 'typescript' ? '#ffffff' : '#a1a1aa',
                    border: 'none', padding: '4px 10px', borderRadius: '4px',
                    fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer',
                  }}
                >
                  TypeScript
                </button>
              </div>

              <button
                onClick={copyCode}
                style={{
                  background: 'none', border: 'none', color: copied ? '#4ade80' : '#a1a1aa',
                  fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer',
                }}
              >
                {copied ? <Check size={13} /> : <Copy size={13} />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            </div>

            <pre style={{ margin: 0, padding: '20px', borderRadius: 0, border: 'none', fontSize: '0.82rem', lineHeight: 1.6 }}>
              <code>{codeExamples[lang]}</code>
            </pre>
          </div>

          {/* Service Endpoints & Rate Limits */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div className="surface-card" style={{ padding: '20px', background: '#ffffff' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Primary Endpoints
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: 'var(--bg-subtle)', borderRadius: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}>
                    <span style={{ color: '#2563eb', fontWeight: 700 }}>POST</span>
                    <span>/chat</span>
                  </div>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>text/plain stream</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: 'var(--bg-subtle)', borderRadius: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}>
                    <span style={{ color: '#059669', fontWeight: 700 }}>GET</span>
                    <span>/health</span>
                  </div>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>200 OK Readiness</span>
                </div>
              </div>
            </div>

            <div className="surface-card" style={{ padding: '20px', background: '#ffffff' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Active Middleware
              </div>
              <p style={{ fontSize: '0.84rem', color: 'var(--text-body)', lineHeight: 1.6 }}>
                <strong>Rate Limiting</strong>: Redis middleware enforces a sliding window of 5 requests per 60 seconds per <code>thread_id</code> or client IP. Returns HTTP 429 when exceeded.
              </p>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 860px) {
          #api div[style*="grid-template-columns: 1.2fr 0.8fr"] {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </section>
  );
}
