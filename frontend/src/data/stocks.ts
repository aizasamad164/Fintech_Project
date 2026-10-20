// MOCK DATA — used only while VITE_USE_MOCK=true.
// Once the backend is connected, real stocks come from /api/v1/recommend.
import type { StockDef } from '../types/portfolio'

export const STOCKS: Record<string, StockDef[]> = {
  Technology: [
    { ticker: 'MSFT', name: 'Microsoft Corp.', sector: 'Technology', riskClass: 'Conservative', yearReturn: 18.4, trend: [100,103,106,104,108,112,110,114,118,115,119,124], peRatio: 32, volatility: 'Low', sharePrice: 378.50 },
    { ticker: 'AAPL', name: 'Apple Inc.', sector: 'Technology', riskClass: 'Conservative', yearReturn: 14.2, trend: [100,102,104,102,106,110,108,112,115,113,116,114], peRatio: 28, volatility: 'Low', sharePrice: 192.30 },
    { ticker: 'GOOGL', name: 'Alphabet Inc.', sector: 'Technology', riskClass: 'Balanced', yearReturn: 31.2, trend: [100,104,108,105,112,118,114,120,126,122,128,131], peRatio: 24, volatility: 'Medium', sharePrice: 158.20 },
    { ticker: 'NVDA', name: 'Nvidia Corp.', sector: 'Technology', riskClass: 'Aggressive', yearReturn: 68.4, trend: [100,112,125,118,135,148,140,158,172,165,178,168], peRatio: 62, volatility: 'High', sharePrice: 875.40 },
    { ticker: 'META', name: 'Meta Platforms', sector: 'Technology', riskClass: 'Balanced', yearReturn: 42.3, trend: [100,108,115,110,122,130,125,135,142,138,145,142], peRatio: 22, volatility: 'Medium', sharePrice: 502.60 },
  ],
  Healthcare: [
    { ticker: 'JNJ', name: 'Johnson & Johnson', sector: 'Healthcare', riskClass: 'Conservative', yearReturn: 8.2, trend: [100,101,102,100,103,105,103,106,108,107,109,108], peRatio: 16, volatility: 'Low', sharePrice: 152.40 },
    { ticker: 'UNH', name: 'UnitedHealth Group', sector: 'Healthcare', riskClass: 'Conservative', yearReturn: 12.4, trend: [100,102,104,102,105,108,106,109,112,110,113,112], peRatio: 21, volatility: 'Low', sharePrice: 524.80 },
    { ticker: 'ABT', name: 'Abbott Laboratories', sector: 'Healthcare', riskClass: 'Conservative', yearReturn: 9.8, trend: [100,101,103,101,104,107,105,108,110,109,111,110], peRatio: 25, volatility: 'Low', sharePrice: 108.30 },
    { ticker: 'ISRG', name: 'Intuitive Surgical', sector: 'Healthcare', riskClass: 'Aggressive', yearReturn: 24.6, trend: [100,104,108,105,111,117,113,119,125,121,127,125], peRatio: 55, volatility: 'Medium', sharePrice: 412.60 },
    { ticker: 'DXCM', name: 'Dexcom Inc.', sector: 'Healthcare', riskClass: 'Aggressive', yearReturn: 19.3, trend: [100,103,107,104,110,115,111,117,122,119,124,119], peRatio: 48, volatility: 'High', sharePrice: 84.20 },
  ],
  'Renewable Energy': [
    { ticker: 'NEE', name: 'NextEra Energy', sector: 'Renewable Energy', riskClass: 'Conservative', yearReturn: 14.2, trend: [100,102,104,102,106,109,107,110,113,111,114,114], peRatio: 20, volatility: 'Low', sharePrice: 74.20 },
    { ticker: 'FSLR', name: 'First Solar Inc.', sector: 'Renewable Energy', riskClass: 'Balanced', yearReturn: 22.8, trend: [100,103,107,104,110,115,111,117,123,119,125,123], peRatio: 18, volatility: 'Medium', sharePrice: 187.40 },
    { ticker: 'BEP', name: 'Brookfield Renewable', sector: 'Renewable Energy', riskClass: 'Conservative', yearReturn: 11.6, trend: [100,101,103,101,104,107,105,108,111,109,112,112], peRatio: 22, volatility: 'Low', sharePrice: 28.80 },
    { ticker: 'ENPH', name: 'Enphase Energy', sector: 'Renewable Energy', riskClass: 'Aggressive', yearReturn: -18.4, trend: [100,94,88,84,90,95,89,84,88,85,84,82], peRatio: 28, volatility: 'High', sharePrice: 68.40 },
    { ticker: 'RUN', name: 'Sunrun Inc.', sector: 'Renewable Energy', riskClass: 'Aggressive', yearReturn: 8.4, trend: [100,104,109,105,112,118,113,119,124,120,125,108], peRatio: 35, volatility: 'High', sharePrice: 14.80 },
  ],
  Pharmaceuticals: [
    { ticker: 'LLY', name: 'Eli Lilly & Co.', sector: 'Pharmaceuticals', riskClass: 'Balanced', yearReturn: 27.6, trend: [100,104,109,106,113,119,115,121,127,123,129,128], peRatio: 58, volatility: 'Medium', sharePrice: 782.40 },
    { ticker: 'MRK', name: 'Merck & Co.', sector: 'Pharmaceuticals', riskClass: 'Conservative', yearReturn: 9.4, trend: [100,101,103,101,104,106,104,107,109,108,110,109], peRatio: 17, volatility: 'Low', sharePrice: 118.60 },
    { ticker: 'ABBV', name: 'AbbVie Inc.', sector: 'Pharmaceuticals', riskClass: 'Conservative', yearReturn: 13.1, trend: [100,102,104,103,106,108,107,110,112,111,114,113], peRatio: 19, volatility: 'Low', sharePrice: 176.20 },
    { ticker: 'VRTX', name: 'Vertex Pharmaceuticals', sector: 'Pharmaceuticals', riskClass: 'Aggressive', yearReturn: 21.8, trend: [100,105,109,104,112,118,112,119,124,118,125,122], peRatio: 31, volatility: 'Medium', sharePrice: 452.30 },
    { ticker: 'PFE', name: 'Pfizer Inc.', sector: 'Pharmaceuticals', riskClass: 'Aggressive', yearReturn: -6.2, trend: [100,98,96,97,95,93,95,94,92,93,94,94], peRatio: 14, volatility: 'Medium', sharePrice: 27.90 },
  ],
}
STOCKS['Multi-Sector'] = [
  STOCKS['Technology'][0], STOCKS['Technology'][2],
  STOCKS['Healthcare'][0], STOCKS['Healthcare'][3],
  STOCKS['Pharmaceuticals'][0],
  STOCKS['Renewable Energy'][0], STOCKS['Renewable Energy'][1],
]
