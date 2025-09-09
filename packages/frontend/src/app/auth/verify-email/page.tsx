'use client'

import React from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { authApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Mail, CheckCircle, XCircle, Loader2 } from 'lucide-react'

export default function VerifyEmailPage() {
  const [status, setStatus] = React.useState<'verifying' | 'success' | 'error' | 'expired'>('verifying')
  const [email, setEmail] = React.useState('')
  const [error, setError] = React.useState('')
  const [isResending, setIsResending] = React.useState(false)
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token')

  React.useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setStatus('error')
        setError('Invalid or missing verification token.')
        return
      }

      try {
        await authApi.verifyEmail(token)
        setStatus('success')
        // Redirect to login after 3 seconds
        setTimeout(() => {
          router.push('/auth/login?message=Email verified successfully! You can now sign in.')
        }, 3000)
      } catch (error: any) {
        if (error.status === 400 && error.code === 'TOKEN_EXPIRED') {
          setStatus('expired')
          setEmail(error.details?.email || '')
        } else {
          setStatus('error')
          setError(error.message || 'Failed to verify email. Please try again.')
        }
      }
    }

    verifyEmail()
  }, [token, router])

  const handleResendVerification = async () => {
    if (!email) return
    
    setIsResending(true)
    try {
      await authApi.resendVerification(email)
      // Show success message and redirect
      router.push('/auth/login?message=Verification email sent! Please check your inbox.')
    } catch (error: any) {
      setError(error.message || 'Failed to resend verification email.')
    } finally {
      setIsResending(false)
    }
  }

  const renderContent = () => {
    switch (status) {
      case 'verifying':
        return (
          <CardContent className="p-8 text-center">
            <Loader2 className="mx-auto mb-4 h-12 w-12 text-primary-600 animate-spin" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Verifying your email...
            </h2>
            <p className="text-gray-600">
              Please wait while we verify your email address.
            </p>
          </CardContent>
        )

      case 'success':
        return (
          <CardContent className="p-8 text-center">
            <CheckCircle className="mx-auto mb-4 h-12 w-12 text-success-600" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Email verified successfully!
            </h2>
            <p className="text-gray-600 mb-4">
              Your email has been verified. You can now sign in to your account.
            </p>
            <p className="text-sm text-gray-500 mb-6">
              Redirecting to login page...
            </p>
            <Link href="/auth/login">
              <Button>
                Continue to login
              </Button>
            </Link>
          </CardContent>
        )

      case 'expired':
        return (
          <CardContent className="p-8 text-center">
            <Mail className="mx-auto mb-4 h-12 w-12 text-warning-600" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Verification link expired
            </h2>
            <p className="text-gray-600 mb-6">
              The verification link has expired. We can send you a new verification email.
            </p>
            {email && (
              <p className="text-sm text-gray-500 mb-4">
                Send to: <span className="font-medium">{email}</span>
              </p>
            )}
            <div className="space-y-3">
              <Button
                onClick={handleResendVerification}
                loading={isResending}
                disabled={isResending || !email}
                className="w-full"
              >
                {isResending ? 'Sending...' : 'Send new verification email'}
              </Button>
              <Link
                href="/auth/login"
                className="block w-full text-center text-sm text-primary-600 hover:text-primary-500"
              >
                Back to login
              </Link>
            </div>
            {error && (
              <div className="mt-4 text-sm text-error-600 bg-error-50 border border-error-200 rounded-md p-3">
                {error}
              </div>
            )}
          </CardContent>
        )

      case 'error':
        return (
          <CardContent className="p-8 text-center">
            <XCircle className="mx-auto mb-4 h-12 w-12 text-error-600" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Verification failed
            </h2>
            <p className="text-gray-600 mb-6">
              {error || 'We were unable to verify your email address.'}
            </p>
            <div className="space-y-3">
              <Link href="/auth/forgot-password">
                <Button variant="outline" className="w-full">
                  Request new verification
                </Button>
              </Link>
              <Link
                href="/auth/login"
                className="block w-full text-center text-sm text-primary-600 hover:text-primary-500"
              >
                Back to login
              </Link>
            </div>
          </CardContent>
        )

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="mx-auto h-12 w-12 rounded bg-primary-600 flex items-center justify-center">
            <span className="text-white font-bold text-xl">M</span>
          </div>
        </div>
        <Card>
          {renderContent()}
        </Card>
      </div>
    </div>
  )
}