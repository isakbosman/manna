'use client'

import { DashboardLayout } from '../../components/layout/dashboard-layout'
import { BookkeepingDashboard } from '@/components/bookkeeping/BookkeepingDashboard'

export default function BookkeepingPage() {
  return (
    <DashboardLayout
      title="Bookkeeping"
      description="Automated bookkeeping and reconciliation management"
    >
      <BookkeepingDashboard />
    </DashboardLayout>
  )
}