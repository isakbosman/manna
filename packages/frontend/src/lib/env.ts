import { z } from 'zod'

// Define environment variable schema
const envSchema = z.object({
  // Public environment variables (available in browser)
  NEXT_PUBLIC_API_URL: z.string().url().default('http://localhost:8000'),
  NEXT_PUBLIC_APP_URL: z.string().url().default('http://localhost:3000'),
  NEXT_PUBLIC_APP_ENV: z.enum(['development', 'staging', 'production']).default('development'),
  NEXT_PUBLIC_ENABLE_ANALYTICS: z.string().transform(val => val === 'true').default('false'),
  NEXT_PUBLIC_ENABLE_CHAT_SUPPORT: z.string().transform(val => val === 'true').default('false'),
  NEXT_PUBLIC_PLAID_ENV: z.enum(['sandbox', 'development', 'production']).default('sandbox'),
  
  // Optional public variables
  NEXT_PUBLIC_GA_MEASUREMENT_ID: z.string().optional(),
  NEXT_PUBLIC_HOTJAR_ID: z.string().optional(),
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: z.string().optional(),
  
  // Server-side only variables
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.string().transform(val => parseInt(val, 10)).default('3000'),
  SENTRY_DSN: z.string().optional(),
})

// Validate and parse environment variables
function createEnv() {
  const parsed = envSchema.safeParse(process.env)
  
  if (!parsed.success) {
    console.error('Invalid environment variables:', parsed.error.format())
    throw new Error('Invalid environment configuration')
  }
  
  return parsed.data
}

// Export validated environment variables
export const env = createEnv()

// Type-safe environment variables for client components
export const clientEnv = {
  NEXT_PUBLIC_API_URL: env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_APP_URL: env.NEXT_PUBLIC_APP_URL,
  NEXT_PUBLIC_APP_ENV: env.NEXT_PUBLIC_APP_ENV,
  NEXT_PUBLIC_ENABLE_ANALYTICS: env.NEXT_PUBLIC_ENABLE_ANALYTICS,
  NEXT_PUBLIC_ENABLE_CHAT_SUPPORT: env.NEXT_PUBLIC_ENABLE_CHAT_SUPPORT,
  NEXT_PUBLIC_PLAID_ENV: env.NEXT_PUBLIC_PLAID_ENV,
  NEXT_PUBLIC_GA_MEASUREMENT_ID: env.NEXT_PUBLIC_GA_MEASUREMENT_ID,
  NEXT_PUBLIC_HOTJAR_ID: env.NEXT_PUBLIC_HOTJAR_ID,
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY,
}