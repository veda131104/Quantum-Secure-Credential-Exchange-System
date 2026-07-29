import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import ProtectedRoute from '@/components/ProtectedRoute';
import { issuerAPI } from '@/lib/api';
import { getErrorMessage } from '@/lib/errorHandler';
import { useRouter } from 'next/router';

export default function RegisterIssuer() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    organization_name: '',
    organization_type: 'university',
    registration_number: '',
    contact_email: '',
    contact_phone: '',
    address: '',
  });
  const [tempPassword, setTempPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setLoading(true);

    try {
      const response = await issuerAPI.registerIssuer(formData);
      setTempPassword(response.data.temp_password || 'Check backend logs');
      setSuccess(true);

      // Reset form
      setFormData({
        organization_name: '',
        organization_type: 'university',
        registration_number: '',
        contact_email: '',
        contact_phone: '',
        address: '',
      });
    } catch (err: any) {
      setError(getErrorMessage(err, 'Failed to register issuer'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <Head>
        <title>Register Issuer - DigiLocker 2.0</title>
      </Head>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <Link href="/dashboard" className="text-sm text-primary-600 hover:text-primary-700">
            ← Back to Dashboard
          </Link>
        </div>

        <div className="bg-white shadow-lg rounded-lg p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Register New Issuer</h1>
          <p className="text-gray-600 mb-6">
            Register a verified organization as a credential issuer
          </p>

          {error && (
            <div className="mb-4 rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}

          {success && (
            <div className="mb-4 rounded-md bg-green-50 p-4 border border-green-200">
              <div className="flex items-center mb-3">
                <svg className="h-6 w-6 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <h3 className="text-base font-bold text-green-800">✓ Issuer Account Created!</h3>
              </div>
              <div className="mt-3 space-y-3">
                <div className="bg-white border-2 border-green-300 rounded-lg p-3">
                  <p className="text-sm font-semibold text-gray-700 mb-2">Login Credentials (Send to Issuer):</p>
                  <div className="space-y-2">
                    <div>
                      <span className="text-xs text-gray-600">Email:</span>
                      <p className="font-mono text-sm text-gray-900 bg-gray-50 p-2 rounded">{formData.contact_email}</p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-600">Temporary Password:</span>
                      <p className="font-mono text-sm text-gray-900 bg-yellow-50 p-2 rounded border border-yellow-300">
                        {tempPassword}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                  <p className="text-xs font-semibold text-yellow-800 mb-1">⚠️ IMPORTANT:</p>
                  <ul className="text-xs text-yellow-700 space-y-1">
                    <li>• Copy and send these credentials to the issuer</li>
                    <li>• This password will NOT be shown again</li>
                    <li>• Issuer should change password after first login</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="organization_name" className="block text-sm font-medium text-gray-700">
                Organization Name *
              </label>
              <input
                type="text"
                id="organization_name"
                name="organization_name"
                required
                value={formData.organization_name}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="e.g., MIT University"
              />
            </div>

            <div>
              <label htmlFor="organization_type" className="block text-sm font-medium text-gray-700">
                Organization Type *
              </label>
              <select
                id="organization_type"
                name="organization_type"
                value={formData.organization_type}
                onChange={handleChange}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-gray-900 bg-white border border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
              >
                <option value="university">University</option>
                <option value="government">Government</option>
                <option value="company">Company</option>
                <option value="ngo">NGO</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label htmlFor="registration_number" className="block text-sm font-medium text-gray-700">
                Registration Number
              </label>
              <input
                type="text"
                id="registration_number"
                name="registration_number"
                value={formData.registration_number}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="e.g., REG123456"
              />
            </div>

            <div>
              <label htmlFor="contact_email" className="block text-sm font-medium text-gray-700">
                Contact Email *
              </label>
              <input
                type="email"
                id="contact_email"
                name="contact_email"
                required
                value={formData.contact_email}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="admin@organization.com"
              />
            </div>

            <div>
              <label htmlFor="contact_phone" className="block text-sm font-medium text-gray-700">
                Contact Phone
              </label>
              <input
                type="tel"
                id="contact_phone"
                name="contact_phone"
                value={formData.contact_phone}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="+1 234 567 8900"
              />
            </div>

            <div>
              <label htmlFor="address" className="block text-sm font-medium text-gray-700">
                Address
              </label>
              <textarea
                id="address"
                name="address"
                rows={3}
                value={formData.address}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="Organization address"
              />
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <h3 className="text-sm font-medium text-blue-800 mb-2 flex items-center">
                <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                What happens when you register?
              </h3>
              <ul className="text-xs text-blue-700 space-y-1">
                <li>• ✅ Blockchain wallet created automatically</li>
                <li>• ✅ Quantum-safe (PQC) keypair generated</li>
                <li>• ✅ Issuer registered on blockchain</li>
                <li>• ✅ Temporary password generated</li>
                <li>• 📧 You must send the credentials to the issuer</li>
                <li>• 🔐 Issuer should change password after first login</li>
              </ul>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
              >
                {loading ? 'Registering...' : 'Register Issuer'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </ProtectedRoute>
  );
}
