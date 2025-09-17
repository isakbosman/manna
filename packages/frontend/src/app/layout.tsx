import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Providers } from '../components/providers/providers';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

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
      <body className={inter.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}