import Head from 'next/head'
import Link from 'next/link'

export default function Home() {
  return (
    <>
      <Head>
        <title>DigiLocker 2.0 - Quantum-Secure Digital Credentials</title>
        <meta name="description" content="Blockchain-based digital credential management with post-quantum cryptography" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <nav className="bg-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold text-primary-600">DigiLocker 2.0</h1>
              </div>
              <div className="flex items-center space-x-4">
                <Link
                  href="/login"
                  className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Login
                </Link>
                <Link
                  href="/register"
                  className="bg-primary-600 text-white hover:bg-primary-700 px-4 py-2 rounded-md text-sm font-medium"
                >
                  Register
                </Link>
              </div>
            </div>
          </div>
        </nav>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h1 className="text-5xl font-extrabold text-gray-900 sm:text-6xl md:text-7xl">
              Quantum-Secure
              <span className="block text-primary-600">Digital Credentials</span>
            </h1>
            <p className="mt-6 max-w-2xl mx-auto text-xl text-gray-500">
              Next-generation blockchain-based digital credential management with
              Post-Quantum Cryptography, biometric authentication, and decentralized storage.
            </p>
            <div className="mt-10 flex justify-center gap-4">
              <Link
                href="/register"
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                Get Started
              </Link>
              <Link
                href="/verify"
                className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Verify Credential
              </Link>
            </div>
          </div>

          <div className="mt-20 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <div className="bg-white overflow-hidden shadow-lg rounded-lg p-6">
              <div className="text-primary-600 mb-4">
                <svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900">Post-Quantum Security</h3>
              <p className="mt-2 text-base text-gray-500">
                CRYSTALS-Dilithium signatures ensure your credentials are secure against quantum attacks.
              </p>
            </div>

            <div className="bg-white overflow-hidden shadow-lg rounded-lg p-6">
              <div className="text-primary-600 mb-4">
                <svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900">Blockchain Immutability</h3>
              <p className="mt-2 text-base text-gray-500">
                Credentials are anchored on Ethereum blockchain for tamper-proof verification.
              </p>
            </div>

            <div className="bg-white overflow-hidden shadow-lg rounded-lg p-6">
              <div className="text-primary-600 mb-4">
                <svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900">Biometric MFA</h3>
              <p className="mt-2 text-base text-gray-500">
                Face recognition provides secure and convenient multi-factor authentication.
              </p>
            </div>
          </div>
        </div>
      </main>
    </>
  )
}
