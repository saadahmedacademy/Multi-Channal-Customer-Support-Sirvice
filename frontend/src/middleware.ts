import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const ADMIN_KEY = process.env.ADMIN_API_KEY;

export function middleware(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith('/admin')) {
    const cookie = request.cookies.get('admin-api-key');
    if (!cookie || !ADMIN_KEY || cookie.value !== ADMIN_KEY) {
      return NextResponse.redirect(new URL('/', request.url));
    }
  }
  return NextResponse.next();
}

export const config = {
  matcher: '/admin/:path*',
};
