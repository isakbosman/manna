import { redirect } from 'next/navigation'

// Redirect root path to dashboard for authenticated users
// or to auth/login for non-authenticated users
export default function HomePage() {
  redirect('/dashboard')
}
