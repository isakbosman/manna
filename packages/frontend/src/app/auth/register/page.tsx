'use client'

import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { authApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Eye, EyeOff, Mail, Lock, User } from 'lucide-react'

const registerSchema = z.object({
  firstName: z.string().min(2, 'First name must be at least 2 characters'),
  lastName: z.string().min(2, 'Last name must be at least 2 characters'),
  email: z.string().email('Please enter a valid email address'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/(?=.*[a-z])/, 'Password must contain at least one lowercase letter')
    .regex(/(?=.*[A-Z])/, 'Password must contain at least one uppercase letter')
    .regex(/(?=.*\d)/, 'Password must contain at least one number'),
  confirmPassword: z.string(),
  acceptTerms: z.boolean().refine(val => val === true, {
    message: 'You must accept the terms and conditions'
  })
}).refine(data => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword']
})

type RegisterFormData = z.infer<typeof registerSchema>

export default function RegisterPage() {
  const [showPassword, setShowPassword] = React.useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = React.useState(false)
  const [isLoading, setIsLoading] = React.useState(false)
  const [isSuccess, setIsSuccess] = React.useState(false)
  const router = useRouter()

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
    watch
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema)
  })

  const password = watch('password')

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true)
    try {
      await authApi.register({
        firstName: data.firstName,
        lastName: data.lastName,
        email: data.email,
        password: data.password
      })
      setIsSuccess(true)
      // Optionally redirect to login or show success message
      setTimeout(() => {
        router.push('/auth/login?message=Registration successful! Please check your email to verify your account.')
      }, 2000)
    } catch (error: any) {
      setError('root', {
        message: error.message || 'Registration failed. Please try again.'
      })
    } finally {
      setIsLoading(false)
    }
  }

  if (isSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full">
          <Card>
            <CardContent className="p-8 text-center">
              <div className="mx-auto mb-4 h-12 w-12 rounded-full bg-success-100 flex items-center justify-center">
                <svg className="h-6 w-6 text-success-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Account Created Successfully!
              </h2>
              <p className="text-gray-600 mb-4">
                Please check your email to verify your account before signing in.
              </p>
              <p className="text-sm text-gray-500">
                Redirecting to login page...
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Logo and header */}
        <div className="text-center">
          <div className="mx-auto h-12 w-12 rounded bg-primary-600 flex items-center justify-center">
            <span className="text-white font-bold text-xl">M</span>
          </div>
          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Join Manna Financial Platform today
          </p>
        </div>

        {/* Registration form */}
        <Card>
          <CardHeader>
            <CardTitle>Sign Up</CardTitle>
            <CardDescription>
              Enter your information to create your account
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {/* Name fields */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="firstName" className="form-label">
                    First name
                  </label>
                  <Input
                    id="firstName"
                    type="text"
                    placeholder="First name"
                    startIcon={<User className="h-4 w-4" />}
                    error={!!errors.firstName}
                    helperText={errors.firstName?.message}
                    {...register('firstName')}
                  />
                </div>
                <div>
                  <label htmlFor="lastName" className="form-label">
                    Last name
                  </label>
                  <Input
                    id="lastName"
                    type="text"
                    placeholder="Last name"
                    startIcon={<User className="h-4 w-4" />}
                    error={!!errors.lastName}
                    helperText={errors.lastName?.message}
                    {...register('lastName')}
                  />
                </div>
              </div>

              {/* Email field */}
              <div>
                <label htmlFor="email" className="form-label">
                  Email address
                </label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  startIcon={<Mail className="h-4 w-4" />}
                  error={!!errors.email}
                  helperText={errors.email?.message}
                  {...register('email')}
                />
              </div>

              {/* Password field */}
              <div>
                <label htmlFor="password" className="form-label">
                  Password
                </label>
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Create a password"
                  startIcon={<Lock className="h-4 w-4" />}
                  endIcon={
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="text-neutral-400 hover:text-neutral-600"
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  }
                  error={!!errors.password}
                  helperText={errors.password?.message}
                  {...register('password')}
                />
                {/* Password strength indicator */}
                {password && (
                  <div className="mt-2">
                    <div className="text-xs text-gray-600 mb-1">Password strength:</div>
                    <div className="flex space-x-1">
                      <div className={`h-1 w-1/4 rounded ${password.length >= 8 ? 'bg-green-500' : 'bg-gray-300'}`} />
                      <div className={`h-1 w-1/4 rounded ${/(?=.*[a-z])/.test(password) ? 'bg-green-500' : 'bg-gray-300'}`} />
                      <div className={`h-1 w-1/4 rounded ${/(?=.*[A-Z])/.test(password) ? 'bg-green-500' : 'bg-gray-300'}`} />
                      <div className={`h-1 w-1/4 rounded ${/(?=.*\d)/.test(password) ? 'bg-green-500' : 'bg-gray-300'}`} />
                    </div>
                  </div>
                )}
              </div>

              {/* Confirm Password field */}
              <div>
                <label htmlFor="confirmPassword" className="form-label">
                  Confirm password
                </label>
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Confirm your password"
                  startIcon={<Lock className="h-4 w-4" />}
                  endIcon={
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="text-neutral-400 hover:text-neutral-600"
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  }
                  error={!!errors.confirmPassword}
                  helperText={errors.confirmPassword?.message}
                  {...register('confirmPassword')}
                />
              </div>

              {/* Terms and conditions */}
              <div className="flex items-start">
                <div className="flex items-center h-5">
                  <input
                    id="acceptTerms"
                    type="checkbox"
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    {...register('acceptTerms')}
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label htmlFor="acceptTerms" className="text-gray-700">
                    I accept the{' '}
                    <Link href="/terms" className="text-primary-600 hover:text-primary-500">
                      Terms of Service
                    </Link>{' '}
                    and{' '}
                    <Link href="/privacy" className="text-primary-600 hover:text-primary-500">
                      Privacy Policy
                    </Link>
                  </label>
                  {errors.acceptTerms && (
                    <p className="text-error-600 text-xs mt-1">{errors.acceptTerms.message}</p>
                  )}
                </div>
              </div>

              {/* Root error */}
              {errors.root && (
                <div className="text-sm text-error-600 bg-error-50 border border-error-200 rounded-md p-3">
                  {errors.root.message}
                </div>
              )}

              {/* Submit button */}
              <Button
                type="submit"
                className="w-full"
                loading={isLoading}
                disabled={isLoading}
              >
                {isLoading ? 'Creating account...' : 'Create account'}
              </Button>
            </form>

            {/* Additional links */}
            <div className="mt-6 text-center">
              <div className="text-sm text-gray-600">
                Already have an account?{' '}
                <Link
                  href="/auth/login"
                  className="text-primary-600 hover:text-primary-500 font-medium"
                >
                  Sign in
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}