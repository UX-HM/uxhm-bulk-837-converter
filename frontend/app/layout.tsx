import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Bulk 837 Medical Claims Converter',
  description: 'Convert CSV to X12 837P EDI format',
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
