'use client'

import React from 'react'
import Link from 'next/link'
import { useAuth } from '../providers/auth-provider'
import { Button } from '../ui/button'
import {
  User,
  Settings,
  Bell,
  Menu
} from 'lucide-react'

interface HeaderProps {
  onMenuToggle?: () => void
  showMenuButton?: boolean
}

export function Header({ onMenuToggle, showMenuButton = true }: HeaderProps) {
  const { user } = useAuth()
  const [isUserMenuOpen, setIsUserMenuOpen] = React.useState(false)

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        {/* Mobile menu button */}
        {showMenuButton && (
          <Button
            variant="ghost"
            size="icon"
            className="mr-2 md:hidden"
            onClick={onMenuToggle}
          >
            <Menu className="h-5 w-5" />
            <span className="sr-only">Toggle navigation menu</span>
          </Button>
        )}

        {/* Logo */}
        <div className="mr-4 flex">
          <Link href="/dashboard" className="mr-6 flex items-center space-x-2">
            <div className="h-8 w-8 rounded bg-primary-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">M</span>
            </div>
            <span className="hidden font-bold sm:inline-block">
              Manna Financial
            </span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="hidden md:flex items-center space-x-6 text-sm font-medium">
          <Link
            href="/dashboard"
            className="transition-colors hover:text-primary-600"
          >
            Dashboard
          </Link>
          <Link
            href="/transactions"
            className="transition-colors hover:text-primary-600"
          >
            Transactions
          </Link>
          <Link
            href="/accounts"
            className="transition-colors hover:text-primary-600"
          >
            Accounts
          </Link>
          <Link
            href="/reports"
            className="transition-colors hover:text-primary-600"
          >
            Reports
          </Link>
        </nav>

        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          <div className="w-full flex-1 md:w-auto md:flex-none">
            {/* Search could go here */}
          </div>

          {/* Right side actions */}
          <div className="flex items-center space-x-2">
            {/* Notifications */}
            <Button variant="ghost" size="icon">
              <Bell className="h-5 w-5" />
              <span className="sr-only">Notifications</span>
            </Button>

            {/* User menu */}
            <div className="relative">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="relative"
              >
                <User className="h-5 w-5" />
                <span className="sr-only">User menu</span>
              </Button>

              {/* User dropdown menu */}
              {isUserMenuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setIsUserMenuOpen(false)}
                  />
                  <div className="absolute right-0 top-full z-20 mt-1 w-48 rounded-md border bg-popover p-1 text-popover-foreground shadow-md">
                    <div className="px-2 py-1.5 text-sm text-muted-foreground">
                      <p className="font-medium">{user?.firstName} {user?.lastName}</p>
                      <p className="text-xs">{user?.email}</p>
                    </div>
                    <div className="h-px bg-border my-1" />
                    <Link
                      href="/settings"
                      className="flex items-center px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground rounded-sm"
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      <Settings className="mr-2 h-4 w-4" />
                      Settings
                    </Link>
                    {/* Logout removed for local development */}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}