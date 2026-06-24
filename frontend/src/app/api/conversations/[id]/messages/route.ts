import { NextRequest, NextResponse } from 'next/server';
import { forwardBackendResponse, createErrorResponse, getAuthHeaders, getClientIp, checkRateLimit, rateLimitResponse } from '@/lib/api-utils';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const ip = getClientIp(request);
    if (!checkRateLimit(ip)) return rateLimitResponse();

    const { id } = await params;

    if (!UUID_REGEX.test(id)) {
      return NextResponse.json(
        { detail: 'Invalid conversation ID format' },
        { status: 400 }
      );
    }

    const body = await request.json();

    if (!body.content || typeof body.content !== 'string' || body.content.trim().length === 0) {
      return NextResponse.json(
        { detail: 'Message content is required' },
        { status: 400 }
      );
    }

    if (body.content.length > 5000) {
      return NextResponse.json(
        { detail: 'Message content too long' },
        { status: 400 }
      );
    }

    const response = await fetch(`${BACKEND_URL}/conversations/${id}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
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
