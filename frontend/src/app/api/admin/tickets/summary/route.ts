import { NextRequest, NextResponse } from 'next/server';
import { forwardBackendResponse, createErrorResponse, getAuthHeaders } from '@/lib/api-utils';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const days = searchParams.get('days') || '7';

    const response = await fetch(`${BACKEND_URL}/metrics/tickets/summary?days=${days}`, {
      headers: { ...getAuthHeaders(request.cookies) },
    });

    if (!response.ok) {
      return forwardBackendResponse(response, 'Failed to fetch ticket summary');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return createErrorResponse(error, 'Error fetching ticket summary');
  }
}
