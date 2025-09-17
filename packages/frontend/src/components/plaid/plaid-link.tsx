'use client'

import React, { useCallback, useState, useEffect } from 'react'
import { Button } from '../ui/button'
import { Loading } from '../ui/loading'
import { accountsApi } from '../../lib/api/accounts'
import { CreditCard, AlertCircle } from 'lucide-react'

// Define types for Plaid Link
interface PlaidLinkOptions {
  token: string
  onSuccess: (public_token: string, metadata: any) => void
  onExit: (err: any, metadata: any) => void
  onEvent?: (eventName: string, metadata: any) => void
  env: string
}

interface PlaidLinkProps {
  onSuccess: (accounts: any[], institutionName: string) => void
  onError: (error: string) => void
  disabled?: boolean
  className?: string
}

declare global {
  interface Window {
    Plaid?: {
      create: (options: PlaidLinkOptions) => {
        open: () => void
        destroy: () => void
      }
    }
  }
}

export function PlaidLink({ 
  onSuccess, 
  onError, 
  disabled = false,
  className = '' 
}: PlaidLinkProps) {
  const [linkToken, setLinkToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [plaidHandler, setPlaidHandler] = useState<any>(null)

  // Load Plaid script
  useEffect(() => {
    const script = document.createElement('script')
    script.src = 'https://cdn.plaid.com/link/v2/stable/link-initialize.js'
    script.async = true
    script.onload = () => {
      console.log('Plaid script loaded successfully')
    }
    script.onerror = () => {
      console.error('Failed to load Plaid script')
      setError('Failed to load Plaid Link. Please refresh the page.')
    }
    document.body.appendChild(script)

    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script)
      }
    }
  }, [])

  // Get link token from backend
  const getLinkToken = useCallback(async () => {
    console.log('Getting Plaid link token...')
    setIsLoading(true)
    setError(null)

    try {
      const response = await accountsApi.getPlaidLinkToken()
      console.log('Link token received:', response)
      setLinkToken(response.link_token)
    } catch (err: any) {
      console.error('Failed to get link token:', err)
      const errorMessage = err.message || 'Failed to initialize Plaid Link'
      setError(errorMessage)
      onError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }, [onError])

  // Initialize Plaid Link when we have a token
  useEffect(() => {
    console.log('Plaid init check - linkToken:', !!linkToken, 'window.Plaid:', !!window.Plaid)
    if (linkToken && window.Plaid) {
      console.log('Creating Plaid handler with token:', linkToken)
      const handler = window.Plaid.create({
        token: linkToken,
        env: process.env.NEXT_PUBLIC_PLAID_ENV || 'sandbox',
        onSuccess: async (public_token: string, metadata: any) => {
          setIsConnecting(true)
          
          try {
            const response = await accountsApi.exchangePublicToken(public_token, metadata)
            onSuccess(response.accounts, response.institution_name)
          } catch (err: any) {
            const errorMessage = err.message || 'Failed to connect accounts'
            setError(errorMessage)
            onError(errorMessage)
          } finally {
            setIsConnecting(false)
          }
        },
        onExit: (err: any, metadata: any) => {
          if (err != null) {
            const errorMessage = err.error_message || 'Connection cancelled'
            setError(errorMessage)
            onError(errorMessage)
          }
          setIsConnecting(false)
        },
        onEvent: (eventName: string, metadata: any) => {
          console.log('Plaid Link event:', eventName, metadata)
        }
      })
      
      setPlaidHandler(handler)
    }
  }, [linkToken, onSuccess, onError])

  // Cleanup handler on unmount
  useEffect(() => {
    return () => {
      if (plaidHandler) {
        plaidHandler.destroy()
      }
    }
  }, [plaidHandler])

  // Automatically get link token when component mounts
  useEffect(() => {
    getLinkToken()
  }, [getLinkToken])

  const handleConnect = async () => {
    // If no link token yet, get one first
    if (!linkToken) {
      await getLinkToken()
      return
    }

    // If Plaid script isn't loaded yet
    if (!window.Plaid) {
      setError('Plaid is still loading. Please try again in a moment.')
      return
    }

    // If handler exists, open it
    if (plaidHandler) {
      plaidHandler.open()
    } else {
      // Try to create handler again if it doesn't exist
      setError('Initializing Plaid Link...')
      // Trigger re-creation of handler by setting a new link token
      await getLinkToken()
    }
  }

  const isButtonDisabled = disabled || isLoading || isConnecting || !window.Plaid

  return (
    <div className={`space-y-2 ${className}`}>
      <Button
        onClick={handleConnect}
        disabled={isButtonDisabled}
        className="w-full"
        size="lg"
      >
        {isLoading ? (
          <Loading size="sm" className="mr-2" />
        ) : isConnecting ? (
          <Loading size="sm" className="mr-2" />
        ) : (
          <CreditCard className="w-5 h-5 mr-2" />
        )}
        {isLoading 
          ? 'Initializing...' 
          : isConnecting 
            ? 'Connecting...' 
            : 'Connect Bank Account'
        }
      </Button>
      
      {error && (
        <div className="flex items-center text-sm text-error-600 bg-error-50 p-2 rounded-md">
          <AlertCircle className="w-4 h-4 mr-2" />
          {error}
        </div>
      )}
      
      {!window.Plaid && !isLoading && (
        <div className="text-xs text-muted-foreground text-center">
          Loading Plaid Link...
        </div>
      )}
    </div>
  )
}

export default PlaidLink