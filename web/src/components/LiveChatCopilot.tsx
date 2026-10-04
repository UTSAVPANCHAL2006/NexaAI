'use client';

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  Send, Terminal, RefreshCw, Check, Copy, ArrowRight,
  ShieldCheck, Cpu, Database, CheckCircle2, AlertCircle, Sparkles
} from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  isStreaming?: boolean;
  toolInvoked?: string;
}

const scenarioPills = [
  { label: 'ACC-1007 Balance', query: 'What is the current balance for account ACC-1007?' },
  { label: 'TXN-9025 Failure Cause', query: 'Why did transaction TXN-9025 fail?' },
  { label: 'Block Card 4521', query: 'Block card ending in 4521 due to suspected theft' },
  { label: 'user_7 KYC Verification', query: 'Check KYC status and missing documents for user_7' },
  { label: 'UPI Refund Policy', query: 'What is the NPCI refund timeline when a UPI debit occurs without merchant credit?' },
];

export default function LiveChatCopilot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'init-1',
      role: 'assistant',
      content: 'Hello! I am your NexaBank AI Assistant.\n\nI can help you check account balances, manage your cards, troubleshoot transactions, or answer bank policy questions. How can I help you today?',
      timestamp: 'Just now',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [threadId, setThreadId] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'chat' | 'trace'>('chat');
  const [lastTrace, setLastTrace] = useState<string[]>([
    'Security Check: PASS (Verified banking request)',
    'Intent Recognition: Account inquiry detected',
    'Entity Resolution: Linked to account ACC-1007',
    'Action Execution: Fetched real-time balance',
    'Response Delivery: Grounded response generated with masked PII',
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const messageCountRef = useRef<number>(1);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom of the CHAT CONTAINER (not the whole page)
  const scrollToBottom = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    let saved = localStorage.getItem('nexabank_thread_id');
    if (!saved) {
      saved = 'session_' + Math.random().toString(36).substring(2, 9);
      localStorage.setItem('nexabank_thread_id', saved);
    }
    setThreadId(saved);
  }, []);

  const handleResetSession = () => {
    const newId = 'session_' + Math.random().toString(36).substring(2, 9);
    localStorage.setItem('nexabank_thread_id', newId);
    setThreadId(newId);
    setMessages([
      {
        id: 'init-' + Date.now(),
        role: 'assistant',
        content: 'New conversation started. Previous session memory has been reset.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  const copyText = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const sendMessage = async (presetText?: string) => {
    const q = (presetText || input).trim();
    if (!q || loading) return;

    setInput('');
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsgId = 'u-' + Date.now();
    const aiMsgId = 'a-' + Date.now();

    const simulatedTrace = [
      'Guard Node: Regex & keyword verification (PASS)',
      `Classify Node: Category detected (${q.toLowerCase().includes('card') ? 'card_services' : q.toLowerCase().includes('balance') ? 'account_inquiry' : 'policy_rag'})`,
      'Entity Extractor: Extracted parameters and checked session memory',
      `Router Node: Edge -> ${q.toLowerCase().includes('policy') || q.toLowerCase().includes('refund') ? 'Retriever (Qdrant + BM25)' : 'Tool Node (Mock Core Banking)'}`,
      'Generator Node: GPT-4o-mini generation + PII masking',
      'RedisSaver: Checkpointed turn state',
    ];
    setLastTrace(simulatedTrace);

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: 'user', content: q, timestamp: now },
      { id: aiMsgId, role: 'assistant', content: '', timestamp: now, isStreaming: true },
    ]);
    setLoading(true);
    // Scroll to bottom only when user sends a message
    setTimeout(scrollToBottom, 50);

    try {
      let res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticket: q, thread_id: threadId }),
      }).catch(() => null);

      if (!res || !res.ok) {
        throw new Error(`Chat API error: ${res?.status ?? 'No response'}`);
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder('utf-8');
      let fullText = '';

      if (reader) {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          fullText += chunk;
          setMessages((prev) =>
            prev.map((m) => (m.id === aiMsgId ? { ...m, content: fullText, isStreaming: true } : m))
          );
        }
      }

      setMessages((prev) =>
        prev.map((m) => (m.id === aiMsgId ? { ...m, isStreaming: false } : m))
      );
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMsgId
            ? {
                ...m,
                content: `Error connecting to backend (${err.message}). Ensure FastAPI server is running on http://127.0.0.1:8000.`,
                isStreaming: false,
              }
            : m
        )
      );
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  return (
    <div
      id="terminal"
      className="surface-card"
      style={{
        width: '100%',
        maxWidth: '1080px',
        margin: '0 auto',
        overflow: 'hidden',
        border: '1px solid var(--border-hairline)',
        boxShadow: 'var(--shadow-float)',
        display: 'flex',
        flexDirection: 'column',
        height: '620px',
        background: '#ffffff',
      }}
    >
      {/* Workspace Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 18px',
          borderBottom: '1px solid var(--border-hairline)',
          background: '#fafafa',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '6px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#e4e4e7', display: 'inline-block' }} />
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#e4e4e7', display: 'inline-block' }} />
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#e4e4e7', display: 'inline-block' }} />
          </div>
          <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>
            Session: <span style={{ color: 'var(--brand-accent)' }}>{threadId || 'active'}</span>
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ display: 'flex', background: '#f4f4f5', padding: '2px', borderRadius: '6px', border: '1px solid var(--border-hairline)' }}>
            <button
              onClick={() => setActiveTab('chat')}
              style={{
                padding: '4px 10px',
                borderRadius: '4px',
                fontSize: '0.75rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: activeTab === 'chat' ? '#ffffff' : 'transparent',
                color: activeTab === 'chat' ? 'var(--text-main)' : 'var(--text-muted)',
                boxShadow: activeTab === 'chat' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
              }}
            >
              Conversation
            </button>
            <button
              onClick={() => setActiveTab('trace')}
              style={{
                padding: '4px 10px',
                borderRadius: '4px',
                fontSize: '0.75rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: activeTab === 'trace' ? '#ffffff' : 'transparent',
                color: activeTab === 'trace' ? 'var(--text-main)' : 'var(--text-muted)',
                boxShadow: activeTab === 'trace' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
              }}
            >
              Graph Trace
            </button>
          </div>

          <button
            onClick={handleResetSession}
            title="Reset conversation state"
            className="btn-outline"
            style={{ padding: '5px 10px', fontSize: '0.75rem' }}
          >
            <RefreshCw size={12} />
            Reset State
          </button>
        </div>
      </div>

      {/* Main Workspace Body */}
      {activeTab === 'chat' ? (
        <div
          ref={scrollContainerRef}
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '18px',
            background: '#ffffff',
          }}
        >
          {messages.map((m) => {
            const isUser = m.role === 'user';
            return (
              <div
                key={m.id}
                style={{
                  display: 'flex',
                  justifyContent: isUser ? 'flex-end' : 'flex-start',
                }}
              >
                <div style={{ maxWidth: '78%' }}>
                  <div
                    style={{
                      padding: '12px 16px',
                      borderRadius: isUser ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                      background: isUser ? '#09090b' : '#f4f4f5',
                      color: isUser ? '#ffffff' : 'var(--text-main)',
                      fontSize: '0.88rem',
                      lineHeight: 1.6,
                      border: isUser ? 'none' : '1px solid var(--border-hairline)',
                      whiteSpace: 'pre-line',
                      fontFamily: !isUser && (m.content.startsWith('✓') || m.content.startsWith('⚠') || m.content.startsWith('•'))
                        ? 'var(--font-mono)' : 'var(--font-sans)',
                    }}
                  >
                    {m.content ? (
                      <>
                        {m.content}
                        {m.isStreaming && <span className="streaming-cursor" />}
                      </>
                    ) : m.isStreaming ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '2px 0' }}>
                        <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 500 }}>
                          NexaBank AI is typing
                        </span>
                        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                          <span className="typing-dot" />
                          <span className="typing-dot" />
                          <span className="typing-dot" />
                        </div>
                      </div>
                    ) : null}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px', padding: '0 2px' }}>
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                      {m.timestamp}
                    </span>
                    {!isUser && m.content && (
                      <button
                        onClick={() => copyText(m.content, m.id)}
                        style={{
                          background: 'none', border: 'none', cursor: 'pointer',
                          color: copiedId === m.id ? 'var(--brand-success)' : 'var(--text-dim)',
                          fontSize: '0.68rem', display: 'flex', alignItems: 'center', gap: '3px',
                        }}
                      >
                        {copiedId === m.id ? <Check size={11} /> : <Copy size={11} />}
                        <span>{copiedId === m.id ? 'Copied' : 'Copy'}</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>
      ) : (
        /* Execution Trace Tab */
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '24px',
            background: '#09090b',
            color: '#f4f4f5',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.82rem',
          }}
        >
          <div style={{ color: '#a1a1aa', marginBottom: '14px', borderBottom: '1px solid #27272a', paddingBottom: '8px' }}>
            # LangGraph Pipeline Execution State (Thread: {threadId})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {lastTrace.map((step, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                <span style={{ color: '#3b82f6', fontWeight: 600 }}>[{idx + 1}]</span>
                <span style={{ color: idx === 0 ? '#10b981' : '#e4e4e7' }}>{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Query Scenario Pills */}
      <div
        style={{
          display: 'flex',
          gap: '6px',
          padding: '8px 16px',
          background: '#fafafa',
          borderTop: '1px solid var(--border-hairline)',
          overflowX: 'auto',
          whiteSpace: 'nowrap',
        }}
      >
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px', paddingRight: '4px' }}>
          Query presets:
        </span>
        {scenarioPills.map((pill, i) => (
          <button
            key={i}
            onClick={() => sendMessage(pill.query)}
            disabled={loading}
            style={{
              background: '#ffffff',
              border: '1px solid var(--border-hairline)',
              borderRadius: '4px',
              padding: '3px 9px',
              fontSize: '0.75rem',
              color: 'var(--text-body)',
              cursor: 'pointer',
              fontFamily: 'var(--font-mono)',
              transition: 'all 0.15s ease',
              flexShrink: 0,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--text-main)';
              e.currentTarget.style.color = 'var(--text-main)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-hairline)';
              e.currentTarget.style.color = 'var(--text-body)';
            }}
          >
            {pill.label}
          </button>
        ))}
      </div>

      {/* Input box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage();
        }}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '12px 16px',
          background: '#ffffff',
          borderTop: '1px solid var(--border-hairline)',
        }}
      >
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter banking query or test identifier (e.g. 'Balance for ACC-1007')..."
          disabled={loading}
          style={{
            flex: 1,
            padding: '10px 14px',
            borderRadius: '6px',
            border: '1px solid var(--border-hairline)',
            background: '#fafafa',
            fontSize: '0.88rem',
            color: 'var(--text-main)',
            outline: 'none',
            fontFamily: 'var(--font-sans)',
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = 'var(--border-strong)')}
          onBlur={(e) => (e.currentTarget.style.borderColor = 'var(--border-hairline)')}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="btn-solid"
          style={{ padding: '10px 16px', opacity: loading || !input.trim() ? 0.4 : 1 }}
        >
          <Send size={15} />
        </button>
      </form>
    </div>
  );
}
