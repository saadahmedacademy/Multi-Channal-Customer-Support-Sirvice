import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const ADMIN_KEY = process.env.ADMIN_API_KEY;

export async function POST(request: NextRequest) {
  try {
    const { key } = await request.json();

    if (!key || typeof key !== 'string' || !key.trim()) {
      return NextResponse.json(
        { detail: 'API key is required' },
        { status: 400 }
      );
    }

    const res = await fetch(`${BACKEND_URL}/metrics/channels`, {
      headers: { 'X-API-Key': key.trim() },
    });

    if (!res.ok) {
      return NextResponse.json(
        { detail: 'Invalid API key' },
        { status: 401 }
      );
    }

    const isAdmin = !!(ADMIN_KEY && key.trim() === ADMIN_KEY);
    const response = NextResponse.json({ valid: true, isAdmin });
    response.cookies.set('admin-api-key', key.trim(), {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 86400,
    });

    return response;
  } catch {
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    );
  }
}
