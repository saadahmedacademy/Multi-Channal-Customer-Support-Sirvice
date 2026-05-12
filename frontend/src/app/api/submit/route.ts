import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

interface SupportFormSubmission {
  name: string;
  email: string;
  subject: string;
  category: string;
  priority: string;
  message: string;
}

interface SupportFormResponse {
  ticket_id: string;
  message: string;
  estimated_response_time: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: SupportFormSubmission = await request.json();

    // Validate required fields
    if (!body.name || !body.email || !body.subject || !body.message) {
      return NextResponse.json(
        { detail: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(body.email)) {
      return NextResponse.json(
        { detail: 'Invalid email format' },
        { status: 400 }
      );
    }

    // Validate message length
    if (body.message.length < 10) {
      return NextResponse.json(
        { detail: 'Message must be at least 10 characters' },
        { status: 400 }
      );
    }

    // Forward to backend API
    const response = await fetch(`${BACKEND_URL}/support/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: body.name,
        email: body.email,
        subject: body.subject,
        category: body.category || 'general',
        priority: body.priority || 'medium',
        message: body.message,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { detail: errorData.detail || 'Failed to submit support request' },
        { status: response.status }
      );
    }

    const data: SupportFormResponse = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error submitting support form:', error);
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    );
  }
}
