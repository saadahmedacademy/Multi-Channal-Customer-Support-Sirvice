import { NextRequest, NextResponse } from 'next/server';
import { forwardBackendResponse, createErrorResponse, getAuthHeaders, getClientIp, checkRateLimit, rateLimitResponse } from '@/lib/api-utils';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const TICKET_ID_REGEX = /^TICKET-[A-Z0-9]{6,}$/i;

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ ticketId: string }> }
) {
  try {
    const ip = getClientIp(request);
    if (!checkRateLimit(ip)) return rateLimitResponse();

    const { ticketId } = await params;

    if (!ticketId || !TICKET_ID_REGEX.test(ticketId)) {
      return NextResponse.json(
        { detail: 'Invalid ticket ID format' },
        { status: 400 }
      );
    }

    const response = await fetch(`${BACKEND_URL}/support/ticket/${ticketId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    });

    if (!response.ok) {
      return forwardBackendResponse(response, 'Ticket not found');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return createErrorResponse(error, 'Error fetching ticket status');
  }
}
