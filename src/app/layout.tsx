import type {Metadata} from 'next';
import {Geist, Geist_Mono, Poppins} from 'next/font/google';
import './globals.css';
import { ThemeProvider } from 'next-themes'
import  { Providers }  from './providers';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

const poppins = Poppins({
  variable: '--font-poppins',
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
});

// moved to page.tsx to avoid use client issues
// export const metadata: Metadata = {
//   title: 'WicketWise',
//   description: 'Your personal AI IPL data assistant',
// };

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${poppins.variable} ${geistSans.variable} ${geistMono.variable} antialiased`}>
      <Providers >
        {children}
        </Providers>
      </body>
    </html>
  );
}


