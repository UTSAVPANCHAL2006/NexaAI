import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'NexaBank AI — Intelligent Banking Assistant',
  description:
    'Enterprise-grade agentic AI for retail banking. Natural-language chat, hybrid RAG over policy documents, and real-time core-banking tools. Powered by LangGraph, OpenAI, and Qdrant.',
  keywords: ['banking AI', 'customer support AI', 'LangGraph', 'agentic AI', 'banking assistant'],
  openGraph: {
    title: 'NexaBank AI — Intelligent Banking Assistant',
    description: 'Enterprise-grade agentic AI for retail banking.',
    type: 'website',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>{children}</body>
    </html>
  );
}
