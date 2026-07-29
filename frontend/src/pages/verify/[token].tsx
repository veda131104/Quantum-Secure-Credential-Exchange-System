import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { verificationAPI } from '@/lib/api';
import { getErrorMessage } from '@/lib/errorHandler';

export default function VerifyCredential() {
  const router = useRouter();
  const { token } = router.query;
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Debug: Log when component mounts
  useEffect(() => {
    console.log('VerifyCredential component mounted');
    console.log('Router query:', router.query);
    console.log('Token:', token);
    console.log('Router ready:', router.isReady);
  }, []);

  useEffect(() => {
    console.log('Token/router.isReady changed:', { token, isReady: router.isReady });

    if (token && typeof token === 'string') {
      console.log('Verifying credential with token:', token);
      verifyCredential();
    } else if (router.isReady && !token) {
      // Router is ready but no token - show error
      console.log('Router is ready but no token provided');
      setError('No verification token provided');
      setLoading(false);
    }
  }, [token, router.isReady]);

  const verifyCredential = async () => {
    try {
      console.log('Calling verification API...');
      const response = await verificationAPI.verifyCredential(token as string);
      console.log('Verification response:', response.data);
      setResult(response.data);
    } catch (err: any) {
      console.error('Verification error:', err);
      setError(getErrorMessage(err, 'Verification failed'));
    } finally {
      setLoading(false);
    }
  };

  // Debug render state
  console.log('Render state:', { loading, error: !!error, result: !!result });

  if (loading) {
    return (
      <>
        <Head>
          <title>Verifying Credential - DigiLocker 2.0</title>
        </Head>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Verifying credential...</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Head>
        <title>Verify Credential - DigiLocker 2.0</title>
      </Head>
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Credential Verification</h1>
            <p className="mt-2 text-gray-600">Blockchain-verified digital credential</p>
          </div>

          {error ? (
            <div className="bg-white shadow-lg rounded-lg p-8 text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100 mb-4">
                <svg className="h-10 w-10 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Verification Failed</h2>
              <p className="text-gray-600">{error}</p>
            </div>
          ) : result && result.verified ? (
            <div className="bg-white shadow-lg rounded-lg overflow-hidden">
              <div className="bg-green-50 px-6 py-4 border-b border-green-200">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h2 className="text-xl font-bold text-green-900">✓ Credential Verified</h2>
                    <p className="text-sm text-green-700">This credential is authentic and valid</p>
                  </div>
                </div>
              </div>

              <div className="px-6 py-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">
                      Credential Details
                    </h3>
                    <dl className="space-y-2">
                      {result.credential_type && (
                        <div>
                          <dt className="text-xs text-gray-500">Type</dt>
                          <dd className="text-sm font-medium text-gray-900">{result.credential_type}</dd>
                        </div>
                      )}
                      {result.credential_name && (
                        <div>
                          <dt className="text-xs text-gray-500">Name</dt>
                          <dd className="text-sm font-medium text-gray-900">{result.credential_name}</dd>
                        </div>
                      )}
                      {result.issue_date && (
                        <div>
                          <dt className="text-xs text-gray-500">Issue Date</dt>
                          <dd className="text-sm font-medium text-gray-900">
                            {new Date(result.issue_date).toLocaleDateString()}
                          </dd>
                        </div>
                      )}
                      {result.expiry_date && (
                        <div>
                          <dt className="text-xs text-gray-500">Expiry Date</dt>
                          <dd className="text-sm font-medium text-gray-900">
                            {new Date(result.expiry_date).toLocaleDateString()}
                          </dd>
                        </div>
                      )}
                    </dl>
                  </div>

                  {result.issuer_name && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">
                        Issuer Information
                      </h3>
                      <dl className="space-y-2">
                        <div>
                          <dt className="text-xs text-gray-500">Issuer</dt>
                          <dd className="text-sm font-medium text-gray-900">{result.issuer_name}</dd>
                        </div>
                      </dl>
                    </div>
                  )}
                </div>

                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">
                    Verification Status
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="flex items-center">
                      {result.signature_valid ? (
                        <svg className="h-5 w-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="h-5 w-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                      )}
                      <span className="text-sm text-gray-700">Signature Valid</span>
                    </div>
                    <div className="flex items-center">
                      {result.blockchain_verified ? (
                        <svg className="h-5 w-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="h-5 w-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                      )}
                      <span className="text-sm text-gray-700">Blockchain</span>
                    </div>
                    <div className="flex items-center">
                      {!result.is_expired ? (
                        <svg className="h-5 w-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="h-5 w-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                      )}
                      <span className="text-sm text-gray-700">Not Expired</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white shadow-lg rounded-lg p-8 text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-yellow-100 mb-4">
                <svg className="h-10 w-10 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Verification Issues</h2>
              <p className="text-gray-600">{result?.message || 'Unable to verify this credential'}</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
