import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import Link from 'next/link';
import Head from 'next/head';
import { userAPI } from '@/lib/api';

export default function Wallet() {
  const { user } = useAuth();
  const [credentials, setCredentials] = useState<any[]>([]);
  const [wallet, setWallet] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [credentialsRes, walletRes] = await Promise.all([
        userAPI.getCredentials(),
        userAPI.getWallet(),
      ]);
      setCredentials(credentialsRes.data);
      setWallet(walletRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCredentials = credentials.filter((cred) => {
    if (filter === 'active') return cred.is_active;
    if (filter === 'inactive') return !cred.is_active;
    return true;
  });

  return (
    <ProtectedRoute>
      <Head>
        <title>My Wallet - DigiLocker 2.0</title>
      </Head>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">My Credential Wallet</h1>
          <p className="mt-2 text-gray-600">View and manage your digital credentials</p>
        </div>

        {/* Wallet Info */}
        {wallet && (
          <div className="bg-gradient-to-r from-primary-500 to-primary-700 rounded-lg shadow-lg p-6 mb-8 text-white">
            <h2 className="text-xl font-semibold mb-2">Blockchain Wallet</h2>
            <p className="text-sm opacity-90 mb-4">Your credentials are secured on the blockchain</p>
            <div className="bg-white bg-opacity-20 rounded p-3">
              <p className="text-xs opacity-75 mb-1">Wallet Address</p>
              <p className="font-mono text-sm break-all">{wallet.wallet_address}</p>
            </div>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="mb-6">
          <div className="sm:hidden">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
            >
              <option value="all">All Credentials</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
          <div className="hidden sm:block">
            <nav className="flex space-x-4" aria-label="Tabs">
              {[
                { key: 'all', label: 'All Credentials' },
                { key: 'active', label: 'Active' },
                { key: 'inactive', label: 'Inactive' },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setFilter(tab.key)}
                  className={`${
                    filter === tab.key
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-500 hover:text-gray-700'
                  } px-3 py-2 font-medium text-sm rounded-md`}
                >
                  {tab.label}
                  <span className="ml-2 text-xs">
                    ({tab.key === 'all' ? credentials.length : credentials.filter((c) => tab.key === 'active' ? c.is_active : !c.is_active).length})
                  </span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Credentials Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          </div>
        ) : filteredCredentials.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No credentials</h3>
            <p className="mt-1 text-sm text-gray-500">
              {filter === 'all'
                ? 'You don\'t have any credentials yet.'
                : `No ${filter} credentials found.`}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filteredCredentials.map((credential) => (
              <div
                key={credential.id}
                className="bg-white overflow-hidden shadow-lg rounded-lg hover:shadow-xl transition-shadow"
              >
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <svg className="h-8 w-8 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                    </div>
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
                  <h3 className="text-lg font-medium text-gray-900 mb-1">
                    {credential.credential_name}
                  </h3>
                  <p className="text-sm text-gray-500 mb-2">{credential.credential_type}</p>
                  <p className="text-xs text-gray-400 mb-4">Issued by {credential.issuer_name}</p>
                  <div className="border-t border-gray-200 pt-4">
                    <div className="flex justify-between text-xs text-gray-500 mb-2">
                      <span>Issue Date</span>
                      <span>{new Date(credential.issue_date).toLocaleDateString()}</span>
                    </div>
                    {credential.expiry_date && (
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>Expiry Date</span>
                        <span>{new Date(credential.expiry_date).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                  <div className="mt-4 flex space-x-2">
                    <Link
                      href={`/credential/${credential.id}`}
                      className="flex-1 bg-primary-600 text-white text-center px-4 py-2 rounded-md text-sm hover:bg-primary-700"
                    >
                      View Details
                    </Link>
                    <Link
                      href={`/share/${credential.id}`}
                      className="flex-1 bg-gray-100 text-gray-700 text-center px-4 py-2 rounded-md text-sm hover:bg-gray-200"
                    >
                      Share
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
