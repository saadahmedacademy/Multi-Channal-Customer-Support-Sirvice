import { NextRequest, NextResponse } from 'next/server';
import { forwardBackendResponse, createErrorResponse, getAuthHeaders, getClientIp, checkRateLimit, rateLimitResponse } from '@/lib/api-utils';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const VALID_RATINGS = ['thumbs_up', 'thumbs_down'];

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ messageId: string }> }
) {
  try {
    const ip = getClientIp(request);
    if (!checkRateLimit(ip)) return rateLimitResponse();

    const { messageId } = await params;

    if (!UUID_REGEX.test(messageId)) {
      return NextResponse.json(
        { detail: 'Invalid message ID format' },
        { status: 400 }
      );
    }

    const body = await request.json();

    if (!body.rating || !VALID_RATINGS.includes(body.rating)) {
      return NextResponse.json(
        { detail: 'Invalid rating. Must be thumbs_up or thumbs_down' },
        { status: 400 }
      );
    }

    if (body.reason && typeof body.reason === 'string' && body.reason.length > 1000) {
      return NextResponse.json(
        { detail: 'Feedback reason too long' },
        { status: 400 }
      );
    }

    const response = await fetch(`${BACKEND_URL}/conversations/messages/${messageId}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders(request.cookies) },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      return forwardBackendResponse(response, 'Failed to submit feedback');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return createErrorResponse(error, 'Error submitting feedback');
  }
}
