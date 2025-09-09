import { NextRequest, NextResponse } from 'next/server'
import { env } from './lib/env'

export function middleware(request: NextRequest) {
  // Clone the request headers
  const requestHeaders = new Headers(request.headers)
  
  // Check for authentication on protected routes
  const { pathname } = request.nextUrl
  const isAuthPage = pathname.startsWith('/auth')
  const isPublicPage = ['/', '/about', '/contact', '/terms', '/privacy'].includes(pathname)
  const isApiRoute = pathname.startsWith('/api')
  const isProtectedRoute = !isAuthPage && !isPublicPage && !isApiRoute
  
  // Get authentication token from cookies
  const accessToken = request.cookies.get('access_token')?.value
  const isAuthenticated = !!accessToken
  
  // Redirect logic for authentication
  if (isProtectedRoute && !isAuthenticated) {
    const loginUrl = new URL('/auth/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }
  
  // Redirect authenticated users away from auth pages to dashboard
  if (isAuthPage && isAuthenticated && !pathname.includes('/auth/logout')) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }
  
  // Add security headers
  const response = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  })

  // Security headers
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  response.headers.set('X-XSS-Protection', '1; mode=block')
  
  // Content Security Policy
  if (env.NEXT_PUBLIC_APP_ENV === 'production') {
    const csp = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-eval' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com",
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
      "img-src 'self' data: https: blob:",
      "font-src 'self' https://fonts.gstatic.com",
      "connect-src 'self' https://api.manna.com https://www.google-analytics.com https://vitals.vercel-insights.com",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
    ].join('; ')
    
    response.headers.set('Content-Security-Policy', csp)
  }

  // HSTS header for HTTPS
  if (request.nextUrl.protocol === 'https:') {
    response.headers.set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload')
  }

  // Rate limiting for API routes
  if (request.nextUrl.pathname.startsWith('/api/')) {
    const ip = request.ip || request.headers.get('X-Forwarded-For') || 'unknown'
    const rateLimit = checkRateLimit(ip)
    
    if (!rateLimit.allowed) {
      return new NextResponse('Too Many Requests', {
        status: 429,
        headers: {
          'Retry-After': rateLimit.resetTime.toString(),
        },
      })
    }
  }

  // Redirect HTTP to HTTPS in production
  if (env.NEXT_PUBLIC_APP_ENV === 'production' && request.nextUrl.protocol === 'http:') {
    return NextResponse.redirect(`https://${request.nextUrl.host}${request.nextUrl.pathname}${request.nextUrl.search}`)
  }

  return response
}

// Simple in-memory rate limiting (replace with Redis in production)
const rateLimit = new Map<string, { count: number; resetTime: number }>()

function checkRateLimit(ip: string): { allowed: boolean; resetTime: number } {
  const now = Date.now()
  const windowMs = 15 * 60 * 1000 // 15 minutes
  const maxRequests = 100 // requests per window

  const record = rateLimit.get(ip)
  
  if (!record || now > record.resetTime) {
    rateLimit.set(ip, { count: 1, resetTime: now + windowMs })
    return { allowed: true, resetTime: now + windowMs }
  }

  if (record.count >= maxRequests) {
    return { allowed: false, resetTime: record.resetTime }
  }

  record.count++
  return { allowed: true, resetTime: record.resetTime }
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public assets
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}