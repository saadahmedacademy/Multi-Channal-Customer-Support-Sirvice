import { NextRequest, NextResponse } from 'next/server';
import { forwardBackendResponse, createErrorResponse } from '@/lib/api-utils';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

const PHONE_REGEX = /^\+[1-9]\d{1,14}$/;

interface LinkIdentifiersRequest {
  email?: string;
  phone?: string;
}

interface LinkedIdentifier {
  id: string;
  identifier_type: string;
  identifier_value: string;
  verified: boolean;
  created_at: string;
}

interface LinkIdentifiersResponse {
  customer_id: string;
  message: string;
  identifiers: LinkedIdentifier[];
}

export async function POST(request: NextRequest) {
  try {
    const body: LinkIdentifiersRequest = await request.json();

    if (!body.email && !body.phone) {
      return NextResponse.json(
        { detail: 'At least one identifier (email or phone) must be provided' },
        { status: 400 }
      );
    }

    if (body.email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(body.email)) {
        return NextResponse.json(
          { detail: 'Invalid email format' },
          { status: 400 }
        );
      }
    }

    if (body.phone && !PHONE_REGEX.test(body.phone)) {
      return NextResponse.json(
        { detail: 'Invalid phone format. Must be in E.164 format (e.g., +14155551234)' },
        { status: 400 }
      );
    }

    const response = await fetch(`${BACKEND_URL}/customers/link-identifiers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      return forwardBackendResponse(response, 'Failed to link identifiers');
    }

    const data: LinkIdentifiersResponse = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return createErrorResponse(error, 'Error linking customer identifiers');
  }
}
