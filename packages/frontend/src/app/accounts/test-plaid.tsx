'use client'

import { useEffect } from 'react'

export function TestPlaid() {
  useEffect(() => {
    // Check if Plaid script loads
    const checkPlaid = () => {
      console.log('=== Plaid Test ===')
      console.log('window.Plaid exists:', !!window.Plaid)
      if (window.Plaid) {
        console.log('Plaid object:', window.Plaid)
      }
    }

    // Check immediately
    checkPlaid()

    // Check after a delay
    const timer = setTimeout(checkPlaid, 3000)

    // Try to fetch link token
    fetch('http://localhost:8001/api/v1/plaid/create-link-token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
      .then(res => res.json())
      .then(data => {
        console.log('Link token response:', data)
      })
      .catch(err => {
        console.error('Link token error:', err)
      })

    return () => clearTimeout(timer)
  }, [])

  return null
}