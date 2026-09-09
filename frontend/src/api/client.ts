import axios from 'axios';

// NFR-2.1: the frontend only ever talks to our own backend.
// Groq / Finnhub / Polygon keys are never referenced here.
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL as string, // e.g. https://api.yourapp.com
});

export interface PortfolioRequest {
  budget: number;
  risk_strategy: 'conservative' | 'balanced' | 'aggressive';
  sectors: string[];
}

export async function generatePortfolio(payload: PortfolioRequest) {
  const { data } = await apiClient.post('/api/portfolio/generate', payload);
  return data;
}

export default apiClient;
