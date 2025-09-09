import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: {
    default: 'Manna Financial Platform',
    template: '%s | Manna',
  },
  description: 'Financial and Accounting Hub - Agentic Accounting Firm',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}