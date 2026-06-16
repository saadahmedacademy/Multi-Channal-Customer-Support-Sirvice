import { NextRequest, NextResponse } from 'next/server';
import { forwardBackendResponse, createErrorResponse } from '@/lib/api-utils';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json();

    const response = await fetch(`${BACKEND_URL}/conversations/${id}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...body, conversation_id: id }),
    });

    if (!response.ok) {
      return forwardBackendResponse(response, 'Failed to send message');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return createErrorResponse(error, 'Error sending message');
  }
}
