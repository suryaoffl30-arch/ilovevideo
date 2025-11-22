import { Link } from 'react-router-dom';

interface ResultCardProps {
  entityId: string;
  name: string;
  officialDomain: string;
  confidenceScore: number;
  riskLevel: string;
  verificationSources: Array<{
    source_type: string;
    url: string;
    score: number;
  }>;
}

export default function ResultCard({
  entityId,
  name,
  officialDomain,
  confidenceScore,
  riskLevel,
  verificationSources,
}: ResultCardProps) {
  const getBadgeColor = (score: number) => {
    if (score >= 90) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getRiskIcon = (risk: string) => {
    if (risk === 'none') return '✅';
    if (risk === 'low') return '⚠️';
    if (risk === 'medium') return '⚠️';
    return '🚨';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900">{name}</h3>
          <p className="text-gray-600 mt-1">
            <a
              href={`https://${officialDomain}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              {officialDomain}
            </a>
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getBadgeColor(confidenceScore)}`}>
          {confidenceScore.toFixed(1)}
        </span>
      </div>

      <div className="flex items-center mb-4">
        <span className="text-2xl mr-2">{getRiskIcon(riskLevel)}</span>
        <span className="text-sm text-gray-600">
          Risk Level: <span className="font-semibold capitalize">{riskLevel}</span>
        </span>
      </div>

      <div className="mb-4">
        <p className="text-sm text-gray-600 mb-2">Verified by:</p>
        <div className="flex flex-wrap gap-2">
          {verificationSources.map((source, idx) => (
            <span
              key={idx}
              className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-md"
              title={source.url}
            >
              {source.source_type}
            </span>
          ))}
        </div>
      </div>

      <Link
        to={`/entity/${entityId}`}
        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
      >
        View Details →
      </Link>
    </div>
  );
}
