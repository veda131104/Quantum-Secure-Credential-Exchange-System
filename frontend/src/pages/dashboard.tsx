import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import Link from 'next/link';
import Head from 'next/head';
import { userAPI } from '@/lib/api';

export default function Dashboard() {
  const { user } = useAuth();
  const [credentials, setCredentials] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCredentials();
  }, []);

  const fetchCredentials = async () => {
    try {
      const response = await userAPI.getCredentials();
      setCredentials(response.data);
    } catch (error) {
      console.error('Failed to fetch credentials:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>Dashboard - DigiLocker 2.0</title>
      </Head>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.full_name || user?.username}!
          </h1>
          <p className="mt-2 text-gray-600">Manage your digital credentials</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Credentials</dt>
                    <dd className="text-lg font-medium text-gray-900">{credentials.length}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Active</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {credentials.filter((c) => c.is_active).length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Biometric</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {user?.biometric_enrolled ? 'Enrolled' : 'Not Enrolled'}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions - Role Based */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>

          {/* Admin Actions */}
          {user?.role === 'admin' && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 mb-4">
              <Link
                href="/admin/register-issuer"
                className="flex items-center justify-center px-4 py-3 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Register New Issuer
              </Link>
              <Link
                href="/admin/issuers"
                className="flex items-center justify-center px-4 py-3 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Manage Issuers
              </Link>
            </div>
          )}

          {/* Issuer Actions */}
          {user?.role === 'issuer' && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 mb-4">
              <Link
                href="/issuer/issue"
                className="flex items-center justify-center px-4 py-3 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Issue New Credential
              </Link>
              <Link
                href="/issuer/dashboard"
                className="flex items-center justify-center px-4 py-3 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                View Issued Credentials
              </Link>
            </div>
          )}

          {/* User Actions */}
          {user?.role === 'user' && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <Link
                href="/wallet"
                className="flex items-center justify-center px-4 py-3 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
                My Wallet
              </Link>
              {!user?.biometric_enrolled && (
                <Link
                  href="/biometric-enroll"
                  className="flex items-center justify-center px-4 py-3 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
                >
                  <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  Enroll Biometric
                </Link>
              )}
            </div>
          )}

          {/* Common Actions for All */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 mt-4">
            <Link
              href="/verify"
              className="flex items-center justify-center px-4 py-3 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Verify Credential
            </Link>
          </div>
        </div>

        {/* Recent Credentials */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Recent Credentials</h2>
          {loading ? (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            </div>
          ) : credentials.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No credentials yet</p>
          ) : (
            <div className="space-y-4">
              {credentials.slice(0, 5).map((credential) => (
                <Link
                  key={credential.id}
                  href={`/credential/${credential.id}`}
                  className="block border border-gray-200 rounded-lg p-4 hover:border-primary-500 hover:shadow-md transition"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="text-sm font-medium text-gray-900">{credential.credential_name}</h3>
                      <p className="text-sm text-gray-500">{credential.credential_type}</p>
                      <p className="text-xs text-gray-400 mt-1">
                        Issued by {credential.issuer_name} on{' '}
                        {new Date(credential.issue_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      {credential.is_active ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          Inactive
                        </span>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
          {credentials.length > 5 && (
            <div className="mt-4 text-center">
              <Link href="/wallet" className="text-sm text-primary-600 hover:text-primary-700">
                View all credentials →
              </Link>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
