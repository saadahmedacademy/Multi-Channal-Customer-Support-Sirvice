import { NextResponse } from 'next/server';

const requestCounts = new Map<string, number[]>();
const RATE_LIMIT_MAX = 30;
const RATE_LIMIT_WINDOW_MS = 60_000;

export function getAuthHeaders(): Record<string, string> {
  const apiKey = process.env.INTERNAL_API_KEY;
  if (!apiKey) return {};
  return { 'X-API-Key': apiKey };
}

export function getClientIp(request: Request): string {
  const forwarded = request.headers.get('x-forwarded-for');
  return forwarded?.split(',')[0]?.trim()
    || request.headers.get('x-real-ip')
    || 'unknown';
}

export function checkRateLimit(ip: string): boolean {
  const now = Date.now();
  const timestamps = requestCounts.get(ip) || [];
  const recent = timestamps.filter(t => now - t < RATE_LIMIT_WINDOW_MS);
  if (recent.length >= RATE_LIMIT_MAX) return false;
  recent.push(now);
  requestCounts.set(ip, recent);
  return true;
}

export function rateLimitResponse(): NextResponse {
  return NextResponse.json(
    { detail: 'Too many requests. Please try again later.' },
    { status: 429 }
  );
}

export async function forwardBackendResponse(
  response: Response,
  defaultMessage: string
): Promise<NextResponse> {
  const errorData = await response.json().catch(() => ({}));
  return NextResponse.json(
    { detail: errorData.detail || defaultMessage },
    { status: response.status }
  );
}

export function createErrorResponse(error: unknown, defaultMessage: string): NextResponse {
  console.error(defaultMessage, error);
  return NextResponse.json(
    { detail: 'Internal server error' },
    { status: 500 }
  );
}
