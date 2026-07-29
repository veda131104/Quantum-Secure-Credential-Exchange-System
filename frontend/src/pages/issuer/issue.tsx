import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import Link from 'next/link';
import Head from 'next/head';
import { issuerAPI } from '@/lib/api';
import { useRouter } from 'next/router';
import { getErrorMessage } from '@/lib/errorHandler';

export default function IssueCredential() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    user_email: '',
    credential_type: 'Aadhaar',
    credential_name: '',
    credential_number: '',
    issue_date: new Date().toISOString().split('T')[0],
    expiry_date: '',
  });
  const [metadata, setMetadata] = useState<{ key: string; value: string }[]>([]);
  const [document, setDocument] = useState<File | null>(null);
  const [documentBase64, setDocumentBase64] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const credentialTypes = [
    'Aadhaar',
    'PAN Card',
    'Driving License',
    'Passport',
    'Voter ID',
    'Birth Certificate',
    'Degree Certificate',
    'Other',
  ];

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        setError('Only PDF files are allowed');
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }

      setDocument(file);
      setError('');

      const reader = new FileReader();
      reader.onload = () => {
        const base64 = reader.result as string;
        const base64Data = base64.split(',')[1];
        setDocumentBase64(base64Data);
      };
      reader.readAsDataURL(file);
    }
  };

  const addMetadataField = () => {
    setMetadata([...metadata, { key: '', value: '' }]);
  };

  const removeMetadataField = (index: number) => {
    setMetadata(metadata.filter((_, i) => i !== index));
  };

  const updateMetadataField = (index: number, field: 'key' | 'value', value: string) => {
    const newMetadata = [...metadata];
    newMetadata[index][field] = value;
    setMetadata(newMetadata);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    if (!documentBase64) {
      setError('Please upload a document');
      setLoading(false);
      return;
    }

    try {
      const metadataObj: Record<string, string> = {};
      metadata.forEach((item) => {
        if (item.key && item.value) {
          metadataObj[item.key] = item.value;
        }
      });

      const payload = {
        user_email: formData.user_email,
        credential_type: formData.credential_type,
        credential_name: formData.credential_name,
        credential_number: formData.credential_number || null,
        document_base64: documentBase64,
        metadata: Object.keys(metadataObj).length > 0 ? metadataObj : null,
        issue_date: formData.issue_date ? new Date(formData.issue_date).toISOString() : null,
        expiry_date: formData.expiry_date ? new Date(formData.expiry_date).toISOString() : null,
      };

      await issuerAPI.issueCredential(payload);
      setSuccess('Credential issued successfully!');

      setTimeout(() => {
        router.push('/issuer/dashboard');
      }, 2000);
    } catch (err: any) {
      setError(getErrorMessage(err, 'Failed to issue credential'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedRoute allowedRoles={['issuer']}>
      <Head>
        <title>Issue Credential - DigiLocker 2.0</title>
      </Head>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <Link href="/issuer/dashboard" className="text-sm text-primary-600 hover:text-primary-700">
            ← Back to Dashboard
          </Link>
        </div>

        <div className="bg-white shadow-lg rounded-lg p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Issue New Credential</h1>
          <p className="text-gray-600 mb-6">
            Issue a blockchain-verified digital credential to a user
          </p>

          {error && (
            <div className="mb-4 rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}

          {success && (
            <div className="mb-4 rounded-md bg-green-50 p-4">
              <div className="text-sm text-green-800">{success}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* User Email */}
            <div>
              <label htmlFor="user_email" className="block text-sm font-medium text-gray-700">
                Recipient Email *
              </label>
              <input
                type="email"
                id="user_email"
                name="user_email"
                value={formData.user_email}
                onChange={handleInputChange}
                required
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="user@example.com"
              />
            </div>

            {/* Credential Type */}
            <div>
              <label htmlFor="credential_type" className="block text-sm font-medium text-gray-700">
                Credential Type *
              </label>
              <select
                id="credential_type"
                name="credential_type"
                value={formData.credential_type}
                onChange={handleInputChange}
                required
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 bg-white focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              >
                {credentialTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>

            {/* Credential Name */}
            <div>
              <label htmlFor="credential_name" className="block text-sm font-medium text-gray-700">
                Credential Name *
              </label>
              <input
                type="text"
                id="credential_name"
                name="credential_name"
                value={formData.credential_name}
                onChange={handleInputChange}
                required
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="e.g., John Doe - Aadhaar"
              />
            </div>

            {/* Credential Number */}
            <div>
              <label htmlFor="credential_number" className="block text-sm font-medium text-gray-700">
                Credential Number (optional)
              </label>
              <input
                type="text"
                id="credential_number"
                name="credential_number"
                value={formData.credential_number}
                onChange={handleInputChange}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="e.g., XXXX-XXXX-XXXX"
              />
            </div>

            {/* Issue Date */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="issue_date" className="block text-sm font-medium text-gray-700">
                  Issue Date *
                </label>
                <input
                  type="date"
                  id="issue_date"
                  name="issue_date"
                  value={formData.issue_date}
                  onChange={handleInputChange}
                  required
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
              </div>

              {/* Expiry Date */}
              <div>
                <label htmlFor="expiry_date" className="block text-sm font-medium text-gray-700">
                  Expiry Date (optional)
                </label>
                <input
                  type="date"
                  id="expiry_date"
                  name="expiry_date"
                  value={formData.expiry_date}
                  onChange={handleInputChange}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
              </div>
            </div>

            {/* Document Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Document (PDF) *
              </label>
              <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                <div className="space-y-1 text-center">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    stroke="currentColor"
                    fill="none"
                    viewBox="0 0 48 48"
                  >
                    <path
                      d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                      strokeWidth={2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <div className="flex text-sm text-gray-600">
                    <label
                      htmlFor="file-upload"
                      className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
                    >
                      <span>Upload a file</span>
                      <input
                        id="file-upload"
                        name="file-upload"
                        type="file"
                        accept="application/pdf"
                        onChange={handleFileChange}
                        className="sr-only"
                      />
                    </label>
                    <p className="pl-1">or drag and drop</p>
                  </div>
                  <p className="text-xs text-gray-500">PDF up to 10MB</p>
                  {document && (
                    <p className="text-sm text-green-600 mt-2">
                      Selected: {document.name}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Metadata */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Additional Metadata (optional)
                </label>
                <button
                  type="button"
                  onClick={addMetadataField}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  + Add Field
                </button>
              </div>
              {metadata.map((item, index) => (
                <div key={index} className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={item.key}
                    onChange={(e) => updateMetadataField(index, 'key', e.target.value)}
                    placeholder="Key"
                    className="flex-1 border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                  <input
                    type="text"
                    value={item.value}
                    onChange={(e) => updateMetadataField(index, 'value', e.target.value)}
                    placeholder="Value"
                    className="flex-1 border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => removeMetadataField(index)}
                    className="px-3 py-2 text-red-600 hover:text-red-700"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">About Credential Issuance</h3>
                  <div className="mt-2 text-sm text-blue-700">
                    <ul className="list-disc pl-5 space-y-1">
                      <li>Document will be stored on IPFS</li>
                      <li>Credential will be signed with PQC (Dilithium2)</li>
                      <li>Transaction will be recorded on blockchain</li>
                      <li>User will receive email notification</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
              >
                {loading ? 'Issuing Credential...' : 'Issue Credential'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </ProtectedRoute>
  );
}
