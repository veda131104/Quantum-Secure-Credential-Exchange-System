import { useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import Link from 'next/link';
import Head from 'next/head';
import { credentialAPI } from '@/lib/api';
import { getErrorMessage } from '@/lib/errorHandler';

export default function ShareCredential() {
  const router = useRouter();
  const { id } = router.query;
  const [expiryHours, setExpiryHours] = useState(24);
  const [verifierName, setVerifierName] = useState('');
  const [verifierOrg, setVerifierOrg] = useState('');
  const [shareLink, setShareLink] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCreateLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await credentialAPI.createShareLink({
        credential_id: id,
        expiry_hours: expiryHours,
        verifier_info: verifierName || verifierOrg ? {
          name: verifierName,
          organization: verifierOrg,
        } : null,
      });

      setShareLink(response.data.share_url);
    } catch (err: any) {
      setError(getErrorMessage(err, 'Failed to create share link'));
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(shareLink);
    alert('Link copied to clipboard!');
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>Share Credential - DigiLocker 2.0</title>
      </Head>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <Link href={`/credential/${id}`} className="text-sm text-primary-600 hover:text-primary-700">
            ← Back to Credential
          </Link>
        </div>

        <div className="bg-white shadow-lg rounded-lg p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Create Share Link</h1>
          <p className="text-gray-600 mb-6">
            Generate a time-bound link to securely share this credential
          </p>

          {!shareLink ? (
            <form onSubmit={handleCreateLink} className="space-y-6">
              {error && (
                <div className="rounded-md bg-red-50 p-4">
                  <div className="text-sm text-red-800">{error}</div>
                </div>
              )}

              <div>
                <label htmlFor="expiryHours" className="block text-sm font-medium text-gray-700">
                  Link Expiry (hours) *
                </label>
                <select
                  id="expiryHours"
                  value={expiryHours}
                  onChange={(e) => setExpiryHours(Number(e.target.value))}
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                >
                  <option value={1}>1 hour</option>
                  <option value={6}>6 hours</option>
                  <option value={24}>24 hours</option>
                  <option value={72}>3 days</option>
                  <option value={168}>7 days</option>
                </select>
              </div>

              <div>
                <label htmlFor="verifierName" className="block text-sm font-medium text-gray-700">
                  Verifier Name (optional)
                </label>
                <input
                  type="text"
                  id="verifierName"
                  value={verifierName}
                  onChange={(e) => setVerifierName(e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  placeholder="e.g., John Doe"
                />
              </div>

              <div>
                <label htmlFor="verifierOrg" className="block text-sm font-medium text-gray-700">
                  Verifier Organization (optional)
                </label>
                <input
                  type="text"
                  id="verifierOrg"
                  value={verifierOrg}
                  onChange={(e) => setVerifierOrg(e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  placeholder="e.g., ABC Company"
                />
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-3 flex-1">
                    <h3 className="text-sm font-medium text-blue-800">About Share Links</h3>
                    <div className="mt-2 text-sm text-blue-700">
                      <ul className="list-disc pl-5 space-y-1">
                        <li>Links automatically expire after the specified time</li>
                        <li>All verification attempts are logged for audit</li>
                        <li>You can revoke the link anytime before expiry</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Share Link'}
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-6">
              <div className="bg-green-50 border border-green-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-green-800">Share link created successfully!</h3>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Share Link
                </label>
                <div className="flex">
                  <input
                    type="text"
                    readOnly
                    value={shareLink}
                    className="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-l-md border border-gray-300 bg-gray-50 text-sm"
                  />
                  <button
                    onClick={copyToClipboard}
                    className="inline-flex items-center px-4 py-2 border border-l-0 border-gray-300 rounded-r-md bg-gray-50 text-sm font-medium text-gray-700 hover:bg-gray-100"
                  >
                    Copy
                  </button>
                </div>
              </div>

              <div className="flex space-x-4">
                <button
                  onClick={() => {
                    setShareLink('');
                    setVerifierName('');
                    setVerifierOrg('');
                  }}
                  className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 text-sm font-medium"
                >
                  Create Another Link
                </button>
                <Link
                  href={`/credential/${id}`}
                  className="flex-1 bg-gray-100 text-gray-700 text-center px-4 py-2 rounded-md hover:bg-gray-200 text-sm font-medium"
                >
                  Back to Credential
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
