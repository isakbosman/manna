import { env } from './env'

// Sentry error tracking setup
export async function initSentry() {
  if (typeof window !== 'undefined' && env.SENTRY_DSN) {
    const { init, BrowserTracing } = await import('@sentry/nextjs')
    
    init({
      dsn: env.SENTRY_DSN,
      environment: env.NODE_ENV,
      integrations: [
        new BrowserTracing({
          beforeNavigate: context => ({
            ...context,
            name: window.location.pathname,
          }),
        }),
      ],
      tracesSampleRate: env.NODE_ENV === 'production' ? 0.1 : 1.0,
      beforeSend(event, hint) {
        // Filter out development errors in production
        if (env.NODE_ENV === 'production' && hint.originalException?.message?.includes('ChunkLoadError')) {
          return null
        }
        return event
      },
    })
  }
}

// Google Analytics setup
export function initGA() {
  if (typeof window !== 'undefined' && env.NEXT_PUBLIC_GA_MEASUREMENT_ID) {
    const script = document.createElement('script')
    script.src = `https://www.googletagmanager.com/gtag/js?id=${env.NEXT_PUBLIC_GA_MEASUREMENT_ID}`
    script.async = true
    document.head.appendChild(script)

    const inlineScript = document.createElement('script')
    inlineScript.innerHTML = `
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', '${env.NEXT_PUBLIC_GA_MEASUREMENT_ID}', {
        page_title: document.title,
        page_location: window.location.href,
      });
    `
    document.head.appendChild(inlineScript)
  }
}

// Custom performance monitoring
export function trackPageView(url: string) {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('config', env.NEXT_PUBLIC_GA_MEASUREMENT_ID, {
      page_path: url,
    })
  }
}

export function trackEvent(action: string, category: string, label?: string, value?: number) {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', action, {
      event_category: category,
      event_label: label,
      value: value,
    })
  }
}

// Performance metrics collection
export function collectWebVitals() {
  if (typeof window !== 'undefined') {
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS(metric => trackEvent('CLS', 'Web Vitals', undefined, Math.round(metric.value * 1000)))
      getFID(metric => trackEvent('FID', 'Web Vitals', undefined, Math.round(metric.value)))
      getFCP(metric => trackEvent('FCP', 'Web Vitals', undefined, Math.round(metric.value)))
      getLCP(metric => trackEvent('LCP', 'Web Vitals', undefined, Math.round(metric.value)))
      getTTFB(metric => trackEvent('TTFB', 'Web Vitals', undefined, Math.round(metric.value)))
    })
  }
}

// Declare global gtag function
declare global {
  interface Window {
    gtag: (...args: any[]) => void
  }
}