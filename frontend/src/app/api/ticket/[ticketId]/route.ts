import { NextRequest, NextResponse } from 'next/server';
import { forwardBackendResponse, createErrorResponse } from '@/lib/api-utils';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ ticketId: string }> }
) {
  try {
    const { ticketId } = await params;

    if (!ticketId) {
      return NextResponse.json(
        { detail: 'Ticket ID is required' },
        { status: 400 }
      );
    }

    const response = await fetch(`${BACKEND_URL}/support/ticket/${ticketId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
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
