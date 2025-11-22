import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getEntity } from '../api/client';

export default function Entity() {
  const { id } = useParams<{ id: string }>();
  const [entity, setEntity] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadEntity(id);
    }
  }, [id]);

  const loadEntity = async (entityId: string) => {
    try {
      const data = await getEntity(entityId);
      setEntity(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load entity');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !entity) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error || 'Entity not found'}</p>
        </div>
      </div>
    );
  }

  const getBadgeColor = (score: number) => {
    if (score >= 90) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="bg-white rounded-lg shadow-md p-8 mb-6">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{entity.name}</h1>
            {entity.entity_type && (
              <p className="text-gray-600 mt-2">Type: {entity.entity_type}</p>
            )}
          </div>
          <span className={`px-4 py-2 rounded-full text-lg font-semibold ${getBadgeColor(entity.confidence_score)}`}>
            {entity.confidence_score.toFixed(1)}
          </span>
        </div>

        {entity.official_domain && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Official Website</h3>
            <a
              href={`https://${entity.official_domain}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline text-lg"
            >
              {entity.official_domain}
            </a>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <p className="text-sm text-gray-600">Risk Level</p>
            <p className="text-lg font-semibold capitalize">{entity.risk_level}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Status</p>
            <p className="text-lg font-semibold capitalize">{entity.status}</p>
          </div>
        </div>
      </div>

      {/* Verifications */}
      <div className="bg-white rounded-lg shadow-md p-8 mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Verification Sources</h2>
        <div className="space-y-3">
          {entity.verifications.map((v: any, idx: number) => (
            <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <div>
                <p className="font-semibold">{v.source_type}</p>
                {v.source_url && (
                  <a
                    href={v.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline"
                  >
                    View source
                  </a>
                )}
              </div>
              <span className="text-sm text-gray-600">
                Score: {(v.score_contrib * v.weight).toFixed(1)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Domains */}
      <div className="bg-white rounded-lg shadow-md p-8 mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Associated Domains</h2>
        <div className="space-y-2">
          {entity.domains.map((d: any, idx: number) => (
            <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <span className="font-mono">{d.domain}</span>
              <div className="flex gap-2">
                {d.is_primary && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                    Primary
                  </span>
                )}
                {d.https_supported && (
                  <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                    HTTPS
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Similar Domains */}
      {entity.similar_domains && entity.similar_domains.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-yellow-900 mb-4">⚠️ Similar Domains</h2>
          <div className="space-y-2">
            {entity.similar_domains.map((d: any, idx: number) => (
              <div key={idx} className="flex justify-between items-center">
                <span className="font-mono text-sm">{d.domain}</span>
                <span className={`px-2 py-1 rounded text-xs ${
                  d.risk === 'high' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {d.risk} risk
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
