import { useState } from 'react';
import { submitDomain } from '../api/client';

export default function Submit() {
  const [formData, setFormData] = useState({
    submitted_by: '',
    entity_name: '',
    domain: '',
    evidence: '',
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const evidence = formData.evidence ? JSON.parse(formData.evidence) : {};
      await submitDomain({
        submitted_by: formData.submitted_by,
        entity_name: formData.entity_name,
        domain: formData.domain,
        evidence,
      });
      setSuccess(true);
      setFormData({
        submitted_by: '',
        entity_name: '',
        domain: '',
        evidence: '',
      });
    } catch (err: any) {
      setError(err.message || 'Submission failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <div className="bg-white rounded-lg shadow-md p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          Submit a Domain for Verification
        </h1>

        <p className="text-gray-600 mb-8">
          Help us build a comprehensive database of official websites. Submit a domain
          you know to be legitimate.
        </p>

        {success && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <p className="text-green-800">
              ✅ Submission received! We'll review it shortly.
            </p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Email
            </label>
            <input
              type="email"
              required
              value={formData.submitted_by}
              onChange={(e) => setFormData({ ...formData, submitted_by: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="your@email.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Company/Entity Name
            </label>
            <input
              type="text"
              required
              value={formData.entity_name}
              onChange={(e) => setFormData({ ...formData, entity_name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="HDFC Bank"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Official Domain
            </label>
            <input
              type="text"
              required
              value={formData.domain}
              onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="hdfcbank.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Evidence (Optional JSON)
            </label>
            <textarea
              value={formData.evidence}
              onChange={(e) => setFormData({ ...formData, evidence: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              rows={4}
              placeholder='{"note": "Found on official Wikipedia page"}'
            />
            <p className="text-sm text-gray-500 mt-1">
              Provide any supporting evidence as JSON
            </p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Submitting...' : 'Submit Domain'}
          </button>
        </form>
      </div>
    </div>
  );
}
