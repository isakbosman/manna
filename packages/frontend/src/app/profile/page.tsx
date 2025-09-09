'use client'

import React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '@/components/providers/auth-provider'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { User, Mail, Lock, Save, Eye, EyeOff } from 'lucide-react'
import { getInitials } from '@/lib/utils'
import { withAuth } from '@/components/providers/auth-provider'

const profileSchema = z.object({
  firstName: z.string().min(2, 'First name must be at least 2 characters'),
  lastName: z.string().min(2, 'Last name must be at least 2 characters'),
  email: z.string().email('Please enter a valid email address')
})

const passwordSchema = z.object({
  currentPassword: z.string().min(1, 'Current password is required'),
  newPassword: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/(?=.*[a-z])/, 'Password must contain at least one lowercase letter')
    .regex(/(?=.*[A-Z])/, 'Password must contain at least one uppercase letter')
    .regex(/(?=.*\d)/, 'Password must contain at least one number'),
  confirmPassword: z.string()
}).refine(data => data.newPassword === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword']
})

type ProfileFormData = z.infer<typeof profileSchema>
type PasswordFormData = z.infer<typeof passwordSchema>

function ProfilePage() {
  const { user, refetch } = useAuth()
  const [showCurrentPassword, setShowCurrentPassword] = React.useState(false)
  const [showNewPassword, setShowNewPassword] = React.useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = React.useState(false)
  const [isUpdatingProfile, setIsUpdatingProfile] = React.useState(false)
  const [isUpdatingPassword, setIsUpdatingPassword] = React.useState(false)
  const [profileSuccess, setProfileSuccess] = React.useState('')
  const [passwordSuccess, setPasswordSuccess] = React.useState('')

  const profileForm = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      firstName: user?.firstName || '',
      lastName: user?.lastName || '',
      email: user?.email || ''
    }
  })

  const passwordForm = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema)
  })

  // Update form when user data loads
  React.useEffect(() => {
    if (user) {
      profileForm.reset({
        firstName: user.firstName || '',
        lastName: user.lastName || '',
        email: user.email || ''
      })
    }
  }, [user, profileForm])

  const onUpdateProfile = async (data: ProfileFormData) => {
    setIsUpdatingProfile(true)
    setProfileSuccess('')
    try {
      await api.put('/api/v1/users/me', data)
      await refetch()
      setProfileSuccess('Profile updated successfully!')
      setTimeout(() => setProfileSuccess(''), 5000)
    } catch (error: any) {
      profileForm.setError('root', {
        message: error.message || 'Failed to update profile. Please try again.'
      })
    } finally {
      setIsUpdatingProfile(false)
    }
  }

  const onUpdatePassword = async (data: PasswordFormData) => {
    setIsUpdatingPassword(true)
    setPasswordSuccess('')
    try {
      await api.put('/api/v1/users/me/password', {
        currentPassword: data.currentPassword,
        newPassword: data.newPassword
      })
      passwordForm.reset()
      setPasswordSuccess('Password updated successfully!')
      setTimeout(() => setPasswordSuccess(''), 5000)
    } catch (error: any) {
      passwordForm.setError('root', {
        message: error.message || 'Failed to update password. Please try again.'
      })
    } finally {
      setIsUpdatingPassword(false)
    }
  }

  const newPassword = passwordForm.watch('newPassword')

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Account Settings</h1>
        <p className="text-gray-600 mt-2">Manage your account information and security settings</p>
      </div>

      <div className="grid gap-8">
        {/* Profile Information */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-4">
              <div className="h-16 w-16 rounded-full bg-primary-100 flex items-center justify-center">
                <span className="text-2xl font-semibold text-primary-700">
                  {getInitials(`${user.firstName} ${user.lastName}`)}
                </span>
              </div>
              <div>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>Update your personal details</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={profileForm.handleSubmit(onUpdateProfile)} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="firstName" className="form-label">
                    First name
                  </label>
                  <Input
                    id="firstName"
                    type="text"
                    placeholder="First name"
                    startIcon={<User className="h-4 w-4" />}
                    error={!!profileForm.formState.errors.firstName}
                    helperText={profileForm.formState.errors.firstName?.message}
                    {...profileForm.register('firstName')}
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
                    error={!!profileForm.formState.errors.lastName}
                    helperText={profileForm.formState.errors.lastName?.message}
                    {...profileForm.register('lastName')}
                  />
                </div>
              </div>
              
              <div>
                <label htmlFor="email" className="form-label">
                  Email address
                </label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Email address"
                  startIcon={<Mail className="h-4 w-4" />}
                  error={!!profileForm.formState.errors.email}
                  helperText={profileForm.formState.errors.email?.message}
                  {...profileForm.register('email')}
                />
              </div>

              {/* Success message */}
              {profileSuccess && (
                <div className="text-sm text-success-600 bg-success-50 border border-success-200 rounded-md p-3">
                  {profileSuccess}
                </div>
              )}

              {/* Error message */}
              {profileForm.formState.errors.root && (
                <div className="text-sm text-error-600 bg-error-50 border border-error-200 rounded-md p-3">
                  {profileForm.formState.errors.root.message}
                </div>
              )}

              <div className="flex justify-end">
                <Button
                  type="submit"
                  loading={isUpdatingProfile}
                  disabled={isUpdatingProfile}
                  className="w-full md:w-auto"
                >
                  <Save className="mr-2 h-4 w-4" />
                  {isUpdatingProfile ? 'Saving...' : 'Save changes'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Password Update */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-4">
              <div className="h-12 w-12 rounded-full bg-gray-100 flex items-center justify-center">
                <Lock className="h-6 w-6 text-gray-600" />
              </div>
              <div>
                <CardTitle>Change Password</CardTitle>
                <CardDescription>Update your password to keep your account secure</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={passwordForm.handleSubmit(onUpdatePassword)} className="space-y-4">
              <div>
                <label htmlFor="currentPassword" className="form-label">
                  Current password
                </label>
                <Input
                  id="currentPassword"
                  type={showCurrentPassword ? 'text' : 'password'}
                  placeholder="Enter current password"
                  startIcon={<Lock className="h-4 w-4" />}
                  endIcon={
                    <button
                      type="button"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      className="text-neutral-400 hover:text-neutral-600"
                    >
                      {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  }
                  error={!!passwordForm.formState.errors.currentPassword}
                  helperText={passwordForm.formState.errors.currentPassword?.message}
                  {...passwordForm.register('currentPassword')}
                />
              </div>

              <div>
                <label htmlFor="newPassword" className="form-label">
                  New password
                </label>
                <Input
                  id="newPassword"
                  type={showNewPassword ? 'text' : 'password'}
                  placeholder="Enter new password"
                  startIcon={<Lock className="h-4 w-4" />}
                  endIcon={
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="text-neutral-400 hover:text-neutral-600"
                    >
                      {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  }
                  error={!!passwordForm.formState.errors.newPassword}
                  helperText={passwordForm.formState.errors.newPassword?.message}
                  {...passwordForm.register('newPassword')}
                />
                {/* Password strength indicator */}
                {newPassword && (
                  <div className="mt-2">
                    <div className="text-xs text-gray-600 mb-1">Password strength:</div>
                    <div className="flex space-x-1">
                      <div className={`h-1 w-1/4 rounded ${newPassword.length >= 8 ? 'bg-green-500' : 'bg-gray-300'}`} />
                      <div className={`h-1 w-1/4 rounded ${/(?=.*[a-z])/.test(newPassword) ? 'bg-green-500' : 'bg-gray-300'}`} />
                      <div className={`h-1 w-1/4 rounded ${/(?=.*[A-Z])/.test(newPassword) ? 'bg-green-500' : 'bg-gray-300'}`} />
                      <div className={`h-1 w-1/4 rounded ${/(?=.*\d)/.test(newPassword) ? 'bg-green-500' : 'bg-gray-300'}`} />
                    </div>
                  </div>
                )}
              </div>

              <div>
                <label htmlFor="confirmPassword" className="form-label">
                  Confirm new password
                </label>
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Confirm new password"
                  startIcon={<Lock className="h-4 w-4" />}
                  endIcon={
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="text-neutral-400 hover:text-neutral-600"
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  }
                  error={!!passwordForm.formState.errors.confirmPassword}
                  helperText={passwordForm.formState.errors.confirmPassword?.message}
                  {...passwordForm.register('confirmPassword')}
                />
              </div>

              {/* Success message */}
              {passwordSuccess && (
                <div className="text-sm text-success-600 bg-success-50 border border-success-200 rounded-md p-3">
                  {passwordSuccess}
                </div>
              )}

              {/* Error message */}
              {passwordForm.formState.errors.root && (
                <div className="text-sm text-error-600 bg-error-50 border border-error-200 rounded-md p-3">
                  {passwordForm.formState.errors.root.message}
                </div>
              )}

              <div className="flex justify-end">
                <Button
                  type="submit"
                  loading={isUpdatingPassword}
                  disabled={isUpdatingPassword}
                  className="w-full md:w-auto"
                >
                  <Lock className="mr-2 h-4 w-4" />
                  {isUpdatingPassword ? 'Updating...' : 'Update password'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Account Information */}
        <Card>
          <CardHeader>
            <CardTitle>Account Information</CardTitle>
            <CardDescription>Your account details and status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-500">User ID</span>
                <span className="text-sm text-gray-900 font-mono">{user.id}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-500">Role</span>
                <span className="text-sm text-gray-900 capitalize">{user.role}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-500">Member since</span>
                <span className="text-sm text-gray-900">
                  {new Date(user.createdAt).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-500">Last updated</span>
                <span className="text-sm text-gray-900">
                  {new Date(user.updatedAt).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Export protected version
export default withAuth(ProfilePage)