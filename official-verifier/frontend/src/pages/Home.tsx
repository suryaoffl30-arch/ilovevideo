import { useState } from 'react';
import SearchBar from '../components/SearchBar';
import ResultCard from '../components/ResultCard';
import { lookup } from '../api/client';

export default function Home() {
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (query: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await lookup({ query });
      setResults(response.data);
    } catch (err: any) {
      setError(err.message || 'Search failed');
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Verify Official Websites
        </h1>
        <p className="text-lg text-gray-600">
          Protect yourself from scams by verifying official website links
        </p>
      </div>

      <div className="mb-8">
        <SearchBar onSearch={handleSearch} />
      </div>

      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Searching...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {results && !loading && (
        <div className="space-y-6">
          <ResultCard
            entityId={results.entity_id}
            name={results.name}
            officialDomain={results.official_domain}
            confidenceScore={results.confidence_score}
            riskLevel={results.risk_level}
            verificationSources={results.verification_sources}
          />

          {results.similar_domains && results.similar_domains.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-yellow-900 mb-4">
                ⚠️ Similar Domains Detected
              </h3>
              <p className="text-sm text-yellow-800 mb-4">
                These domains look similar and may be scams:
              </p>
              <ul className="space-y-2">
                {results.similar_domains.map((domain: any, idx: number) => (
                  <li key={idx} className="flex items-center justify-between">
                    <span className="font-mono text-sm">{domain.domain}</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      domain.risk === 'high' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {domain.risk} risk
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {!results && !loading && !error && (
        <div className="text-center py-12 text-gray-500">
          <p>Search for a company or domain to verify its official website</p>
        </div>
      )}
    </div>
  );
}
