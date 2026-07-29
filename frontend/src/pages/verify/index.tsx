import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';

export default function VerifyIndex() {
  const router = useRouter();
  const [shareLink, setShareLink] = useState('');
  const [error, setError] = useState('');

  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!shareLink.trim()) {
      setError('Please enter a share link');
      return;
    }

    try {
      // Extract token from the share link
      // Format can be: http://domain/verify/TOKEN or just TOKEN
      let token = shareLink.trim();

      // If it's a full URL, extract the token part
      if (token.includes('/verify/')) {
        const parts = token.split('/verify/');
        token = parts[1] || '';
      } else if (token.includes('verify/')) {
        const parts = token.split('verify/');
        token = parts[1] || '';
      }

      // Remove any trailing slashes or query parameters
      token = token.split('/')[0].split('?')[0];

      if (!token) {
        setError('Invalid share link format');
        return;
      }

      // Navigate to the verify page with the token
      router.push(`/verify/${token}`);
    } catch (err) {
      setError('Invalid share link format');
    }
  };

  return (
    <>
      <Head>
        <title>Verify Credential - DigiLocker 2.0</title>
      </Head>
      <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full">
          <div className="bg-white shadow-lg rounded-lg p-8">
            <div className="text-center mb-6">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-primary-100 mb-4">
                <svg
                  className="h-10 w-10 text-primary-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Verify Credential</h2>
              <p className="text-gray-600">
                Enter a share link to verify a digital credential
              </p>
            </div>

            <form onSubmit={handleVerify} className="space-y-6">
              {error && (
                <div className="rounded-md bg-red-50 p-4">
                  <div className="text-sm text-red-800">{error}</div>
                </div>
              )}

              <div>
                <label htmlFor="shareLink" className="block text-sm font-medium text-gray-700 mb-2">
                  Share Link or Token
                </label>
                <input
                  type="text"
                  id="shareLink"
                  value={shareLink}
                  onChange={(e) => setShareLink(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  placeholder="Paste share link here..."
                />
                <p className="mt-2 text-xs text-gray-500">
                  You can paste the complete URL or just the token
                </p>
              </div>

              <button
                type="submit"
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Verify Credential
              </button>
            </form>

            <div className="mt-6 pt-6 border-t border-gray-200">
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <h3 className="text-sm font-medium text-blue-800 mb-2">How it works</h3>
                <ul className="text-xs text-blue-700 space-y-1">
                  <li>• Credential owners generate secure share links</li>
                  <li>• Share links are time-bound and can be revoked</li>
                  <li>• Verification uses blockchain and quantum-safe cryptography</li>
                  <li>• All verification attempts are logged for audit</li>
                </ul>
              </div>
            </div>

            <div className="mt-6 text-center">
              <Link
                href="/"
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                ← Back to Homepage
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
