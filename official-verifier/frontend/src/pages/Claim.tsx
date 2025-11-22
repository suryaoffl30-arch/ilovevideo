import { useState } from 'react';

export default function Claim() {
  const [step, setStep] = useState<'select' | 'verify'>('select');
  const [method, setMethod] = useState<'dns' | 'html' | 'email'>('dns');
  const [token, setToken] = useState('');

  const handleInitiate = () => {
    // Generate a mock token for demonstration
    const mockToken = `verify-${Math.random().toString(36).substring(7)}`;
    setToken(mockToken);
    setStep('verify');
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <div className="bg-white rounded-lg shadow-md p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          Claim Your Brand
        </h1>

        <p className="text-gray-600 mb-8">
          Verify ownership of your domain to manage your brand's listing.
        </p>

        {step === 'select' && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Verification Method
              </label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value as any)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="dns">DNS TXT Record</option>
                <option value="html">HTML File Upload</option>
                <option value="email">Email Verification</option>
              </select>
            </div>

            <button
              onClick={handleInitiate}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Start Verification
            </button>
          </div>
        )}

        {step === 'verify' && (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="font-semibold text-blue-900 mb-4">
                {method === 'dns' && 'Add DNS TXT Record'}
                {method === 'html' && 'Upload HTML File'}
                {method === 'email' && 'Check Your Email'}
              </h3>

              {method === 'dns' && (
                <div>
                  <p className="text-sm text-blue-800 mb-4">
                    Add the following TXT record to your domain's DNS:
                  </p>
                  <div className="bg-white p-4 rounded border border-blue-300 font-mono text-sm">
                    <p>Name: _verification</p>
                    <p>Type: TXT</p>
                    <p>Value: {token}</p>
                  </div>
                </div>
              )}

              {method === 'html' && (
                <div>
                  <p className="text-sm text-blue-800 mb-4">
                    Upload this file to your website root:
                  </p>
                  <div className="bg-white p-4 rounded border border-blue-300 font-mono text-sm">
                    <p>File: verification-{token}.html</p>
                    <p>Content: {token}</p>
                  </div>
                </div>
              )}

              {method === 'email' && (
                <div>
                  <p className="text-sm text-blue-800">
                    We've sent a verification link to your domain's admin email.
                    Click the link to complete verification.
                  </p>
                </div>
              )}
            </div>

            <button
              onClick={() => alert('Verification check would happen here')}
              className="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              Verify Now
            </button>

            <button
              onClick={() => setStep('select')}
              className="w-full px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              Back
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
