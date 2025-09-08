import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Manna Financial Platform',
  description: 'Financial and Accounting Hub - Agentic Accounting Firm',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
