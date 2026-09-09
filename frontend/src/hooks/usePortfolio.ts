import { useState } from 'react';
import { generatePortfolio, PortfolioRequest } from '../api/client';

// FR-6.2: supports real-time re-generation on risk/budget toggle changes.
export function usePortfolio() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate(request: PortfolioRequest) {
    setLoading(true);
    setError(null);
    try {
      const result = await generatePortfolio(request);
      setData(result);
    } catch (err) {
      setError('Failed to generate portfolio. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return { data, loading, error, generate };
}
