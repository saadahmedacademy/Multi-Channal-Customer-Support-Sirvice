import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

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

    // Validate input
    if (!body.email && !body.phone) {
      return NextResponse.json(
        { detail: 'At least one identifier (email or phone) must be provided' },
        { status: 400 }
      );
    }

    // Validate email format if provided
    if (body.email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(body.email)) {
        return NextResponse.json(
          { detail: 'Invalid email format' },
          { status: 400 }
        );
      }
    }

    // Forward to backend API
    const response = await fetch(`${BACKEND_URL}/customers/link-identifiers`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { detail: errorData.detail || 'Failed to link identifiers' },
        { status: response.status }
      );
    }

    const data: LinkIdentifiersResponse = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error linking customer identifiers:', error);
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    );
  }
}
