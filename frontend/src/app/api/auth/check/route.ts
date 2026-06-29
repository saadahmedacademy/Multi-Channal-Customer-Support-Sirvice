import { NextRequest, NextResponse } from 'next/server';

const ADMIN_KEY = process.env.ADMIN_API_KEY;

export async function GET(request: NextRequest) {
  const adminKey = request.cookies.get('admin-api-key')?.value;
  return NextResponse.json({
    keyPresent: !!adminKey,
    isAdmin: !!(ADMIN_KEY && adminKey === ADMIN_KEY),
  });
}
