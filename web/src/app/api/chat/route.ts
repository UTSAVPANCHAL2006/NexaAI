import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { ticket, thread_id } = body;

    if (!ticket) {
      return NextResponse.json({ error: 'Ticket message is required' }, { status: 400 });
    }

    const backendUrl = process.env.BACKEND_API_URL || 'http://127.0.0.1:8000';
    
    // Call FastAPI backend
    const res = await fetch(`${backendUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Thread-ID': thread_id || 'web-default-thread',
      },
      body: JSON.stringify({
        ticket,
        thread_id: thread_id || 'web-default-thread',
      }),
    });

    if (!res.ok) {
      const errText = await res.text();
      return new NextResponse(errText || `Backend returned status ${res.status}`, {
        status: res.status,
        headers: { 'Content-Type': 'text/plain; charset=utf-8' },
      });
    }

    // Stream response back to client
    return new NextResponse(res.body, {
      status: 200,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Transfer-Encoding': 'chunked',
        'Cache-Control': 'no-cache, no-transform',
      },
    });
  } catch (err: any) {
    console.error('Chat API error:', err);
    return new NextResponse(
      `FastAPI Connection Error: ${err.message}. Make sure backend server is running on http://127.0.0.1:8000.`,
      { status: 502, headers: { 'Content-Type': 'text/plain; charset=utf-8' } }
    );
  }
}
