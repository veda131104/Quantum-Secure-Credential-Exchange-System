import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import Link from 'next/link';
import Head from 'next/head';
import { userAPI, credentialAPI } from '@/lib/api';

export default function CredentialDetails() {
  const router = useRouter();
  const { id } = router.query;
  const [credential, setCredential] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchCredential();
    }
  }, [id]);

  const fetchCredential = async () => {
    try {
      const response = await userAPI.getCredentialDetails(id as string);
      setCredential(response.data);
    } catch (error) {
      console.error('Failed to fetch credential:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadDocument = async () => {
    try {
      const response = await credentialAPI.downloadDocument(id as string);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${credential.credential_name}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to download document:', error);
      alert('Failed to download document');
    }
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </ProtectedRoute>
    );
  }

  if (!credential) {
    return (
      <ProtectedRoute>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900">Credential not found</h3>
            <Link href="/wallet" className="text-primary-600 hover:text-primary-700 mt-2 inline-block">
              ← Back to Wallet
            </Link>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <Head>
        <title>{credential.credential_name} - DigiLocker 2.0</title>
      </Head>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <Link href="/wallet" className="text-sm text-primary-600 hover:text-primary-700">
            ← Back to Wallet
          </Link>
        </div>

        <div className="bg-white shadow-lg rounded-lg overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-primary-500 to-primary-700 px-6 py-8 text-white">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold">{credential.credential_name}</h1>
                <p className="mt-2 text-primary-100">{credential.credential_type}</p>
              </div>
              <div>
                {credential.is_active && !credential.is_revoked ? (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                    ✓ Verified
                  </span>
                ) : (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                    ✗ Inactive
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Details */}
          <div className="px-6 py-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">
                  Credential Information
                </h3>
                <dl className="space-y-3">
                  {credential.credential_number && (
                    <div>
                      <dt className="text-sm text-gray-500">Credential Number</dt>
                      <dd className="text-sm font-medium text-gray-900">{credential.credential_number}</dd>
                    </div>
                  )}
                  <div>
                    <dt className="text-sm text-gray-500">Issue Date</dt>
                    <dd className="text-sm font-medium text-gray-900">
                      {new Date(credential.issue_date).toLocaleDateString()}
                    </dd>
                  </div>
                  {credential.expiry_date && (
                    <div>
                      <dt className="text-sm text-gray-500">Expiry Date</dt>
                      <dd className="text-sm font-medium text-gray-900">
                        {new Date(credential.expiry_date).toLocaleDateString()}
                      </dd>
                    </div>
                  )}
                </dl>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">
                  Issuer Information
                </h3>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-sm text-gray-500">Issuer Name</dt>
                    <dd className="text-sm font-medium text-gray-900">{credential.issuer.name}</dd>
                  </div>
                  {credential.issuer.organization_type && (
                    <div>
                      <dt className="text-sm text-gray-500">Organization Type</dt>
                      <dd className="text-sm font-medium text-gray-900">{credential.issuer.organization_type}</dd>
                    </div>
                  )}
                </dl>
              </div>
            </div>

            {/* Blockchain Info */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">
                Blockchain Verification
              </h3>
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm text-gray-500">Transaction Hash</dt>
                  <dd className="text-sm font-mono text-gray-900 break-all">
                    {credential.blockchain_tx_hash || 'Not recorded on blockchain'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Blockchain Verified</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {credential.blockchain_tx_hash ? (
                      credential.blockchain_verified ? (
                        <span className="text-green-600">✓ Verified on Blockchain</span>
                      ) : (
                        <span className="text-yellow-600">⚠ Verification Pending</span>
                      )
                    ) : (
                      <span className="text-gray-500">○ Blockchain not used</span>
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">IPFS CID</dt>
                  <dd className="text-sm font-mono text-gray-900 break-all">
                    {credential.ipfs_cid || 'Not stored on IPFS'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Signature Algorithm</dt>
                  <dd className="text-sm font-medium text-gray-900">{credential.signature_algorithm}</dd>
                </div>
              </dl>
            </div>

            {/* Metadata */}
            {credential.metadata && Object.keys(credential.metadata).length > 0 && (
              <div className="mt-8 pt-6 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">
                  Additional Information
                </h3>
                <dl className="space-y-3">
                  {Object.entries(credential.metadata).map(([key, value]) => (
                    <div key={key}>
                      <dt className="text-sm text-gray-500">{key}</dt>
                      <dd className="text-sm font-medium text-gray-900">{String(value)}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}

            {/* Actions */}
            <div className="mt-8 pt-6 border-t border-gray-200 flex space-x-4">
              <button
                onClick={downloadDocument}
                className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 text-sm font-medium"
              >
                Download Document
              </button>
              <Link
                href={`/share/${credential.id}`}
                className="flex-1 bg-gray-100 text-gray-700 text-center px-4 py-2 rounded-md hover:bg-gray-200 text-sm font-medium"
              >
                Create Share Link
              </Link>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
