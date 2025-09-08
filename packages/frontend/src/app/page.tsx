import { formatCurrency } from '@manna/shared';

export default function HomePage() {
  const sampleAmount = 12345.67;

  return (
    <main>
      <h1>Manna Financial Platform</h1>
      <p>Welcome to your Financial and Accounting Hub</p>
      <p>Sample formatted currency: {formatCurrency(sampleAmount)}</p>
    </main>
  );
}
