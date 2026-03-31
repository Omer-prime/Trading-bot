import type { ReactNode } from 'react';

export const metadata = {
  title: 'Auto Gold Bot Admin',
  description: 'Admin dashboard for managing clients, accounts, and bot workers',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: 'Arial, sans-serif', background: '#0b1220', color: '#e5e7eb' }}>
        {children}
      </body>
    </html>
  );
}
