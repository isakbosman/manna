'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { authApi, isAuthenticated, clearAuthTokens } from '@/lib/api'
import { useRouter, usePathname } from 'next/navigation'

// Types
interface User {
  id: string
  email: string
  firstName: string
  lastName: string
  role: string
  createdAt: string
  updatedAt: string
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: { email: string; password: string; rememberMe?: boolean }) => Promise<void>
  logout: () => Promise<void>
  refetch: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Auth provider component
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isClient, setIsClient] = useState(false)
  const router = useRouter()
  const pathname = usePathname()
  
  // Check if user is authenticated on client
  const authenticated = isClient ? isAuthenticated() : false
  
  // Fetch current user data
  const { 
    data: user, 
    isLoading, 
    refetch,
    error
  } = useQuery({
    queryKey: ['currentUser'],
    queryFn: authApi.getCurrentUser,
    enabled: authenticated && isClient,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })

  useEffect(() => {
    setIsClient(true)
  }, [])

  // Handle authentication errors
  useEffect(() => {
    if (error && authenticated) {
      clearAuthTokens()
      // Don't redirect if already on auth pages
      if (!pathname.startsWith('/auth')) {
        router.push('/auth/login')
      }
    }
  }, [error, authenticated, pathname, router])

  // Login function
  const login = async (credentials: { email: string; password: string; rememberMe?: boolean }) => {
    try {
      await authApi.login(credentials)
      await refetch()
      
      // Check for redirect parameter in URL
      const urlParams = new URLSearchParams(window.location.search)
      const redirectTo = urlParams.get('redirect') || '/dashboard'
      router.push(redirectTo)
    } catch (error) {
      throw error
    }
  }

  // Logout function
  const logout = async () => {
    try {
      await authApi.logout()
      router.push('/auth/login')
    } catch (error) {
      console.error('Logout error:', error)
      // Still redirect to login even if logout request fails
      router.push('/auth/login')
    }
  }

  const contextValue: AuthContextType = {
    user: user || null,
    isLoading: !isClient || isLoading,
    isAuthenticated: authenticated && !!user,
    login,
    logout,
    refetch,
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  )
}

// Hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// HOC to protect routes
export function withAuth<P extends object>(
  Component: React.ComponentType<P>
) {
  return function AuthenticatedComponent(props: P) {
    const { isAuthenticated, isLoading } = useAuth()
    const router = useRouter()

    useEffect(() => {
      if (!isLoading && !isAuthenticated) {
        const currentPath = window.location.pathname
        const redirectUrl = `/auth/login${currentPath !== '/' ? `?redirect=${currentPath}` : ''}`
        router.push(redirectUrl)
      }
    }, [isAuthenticated, isLoading, router])

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      )
    }

    if (!isAuthenticated) {
      return null
    }

    return <Component {...props} />
  }
}