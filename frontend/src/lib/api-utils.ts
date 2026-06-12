import { NextResponse } from 'next/server';

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
