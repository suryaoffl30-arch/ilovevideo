import { useState } from 'react';
import './App.css';

interface VerifyResult {
  verified: boolean;
  official_url: string | null;
  name: string | null;
  confidence: number;
  warning: string | null;
}

interface SearchResult {
  name: string;
  official_url: string;
  domain: string;
  category: string;
}

function App() {
  const [url, setUrl] = useState('');
  const [searchName, setSearchName] = useState('');
  const [verifyResult, setVerifyResult] = useState<VerifyResult | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  const API_URL = 'http://localhost:8000';

  const verifyUrl = async () => {
    if (!url) return;
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const data = await response.json();
      setVerifyResult(data);
    } catch (error) {
      console.error('Error:', error);
    }
    setLoading(false);
  };

  const searchWebsite = async () => {
    if (!searchName) return;
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: searchName })
      });
      const data = await response.json();
      setSearchResults(data.results);
    } catch (error) {
      console.error('Error:', error);
    }
    setLoading(false);
  };

  return (
    <div className="app">
      <header>
        <h1>🔒 Website Verifier</h1>
        <p>Verify official websites and protect yourself from scams</p>
      </header>

      <main>
        <section className="verify-section">
          <h2>Verify a URL</h2>
          <div className="input-group">
            <input
              type="text"
              placeholder="Enter URL (e.g., https://paypal.com)"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && verifyUrl()}
            />
            <button onClick={verifyUrl} disabled={loading}>
              {loading ? 'Checking...' : 'Verify'}
            </button>
          </div>

          {verifyResult && (
            <div className={`result ${verifyResult.verified ? 'verified' : 'warning'}`}>
              {verifyResult.verified ? (
                <>
                  <div className="icon">✅</div>
                  <h3>Verified Official Website</h3>
                  <p><strong>{verifyResult.name}</strong></p>
                  <p>Official URL: <a href={verifyResult.official_url!} target="_blank" rel="noopener noreferrer">
                    {verifyResult.official_url}
                  </a></p>
                </>
              ) : (
                <>
                  <div className="icon">⚠️</div>
                  <h3>Warning</h3>
                  <p>{verifyResult.warning}</p>
                  {verifyResult.official_url && (
                    <p>Official URL: <a href={verifyResult.official_url} target="_blank" rel="noopener noreferrer">
                      {verifyResult.official_url}
                    </a></p>
                  )}
                </>
              )}
            </div>
          )}
        </section>

        <section className="search-section">
          <h2>Search Official Websites</h2>
          <div className="input-group">
            <input
              type="text"
              placeholder="Search by company name (e.g., PayPal)"
              value={searchName}
              onChange={(e) => setSearchName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && searchWebsite()}
            />
            <button onClick={searchWebsite} disabled={loading}>
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>

          {searchResults.length > 0 && (
            <div className="search-results">
              <h3>Found {searchResults.length} result(s)</h3>
              {searchResults.map((result, index) => (
                <div key={index} className="search-result-item">
                  <h4>{result.name}</h4>
                  <p>Category: {result.category}</p>
                  <a href={result.official_url} target="_blank" rel="noopener noreferrer">
                    {result.official_url}
                  </a>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
