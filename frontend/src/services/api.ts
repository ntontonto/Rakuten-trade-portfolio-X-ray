// API Client for Portfolio X-Ray Backend

import axios from 'axios';
import type {
  Portfolio,
  PortfolioSummary,
  Holding,
  PortfolioMetrics,
  UploadResponse,
  PriceHistoryResponse,
  PortfolioTimelineResponse,
  AIInsightResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const portfolioAPI = {
  // Upload CSV files
  uploadCSV: async (files: FileList): Promise<UploadResponse> => {
    const formData = new FormData();
    Array.from(files).forEach((file) => {
      formData.append('files', file);
    });

    const response = await api.post<UploadResponse>('/upload/csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Get portfolio summary
  getSummary: async (portfolioId: string): Promise<PortfolioSummary> => {
    const response = await api.get<PortfolioSummary>(`/portfolios/${portfolioId}/summary`);
    return response.data;
  },

  // Get holdings
  getHoldings: async (portfolioId: string): Promise<Holding[]> => {
    const response = await api.get<Holding[]>(`/portfolios/${portfolioId}/holdings`);
    return response.data;
  },

  // Update holding price
  updateHoldingPrice: async (
    portfolioId: string,
    symbol: string,
    newPrice: number
  ): Promise<Holding> => {
    const response = await api.put<Holding>(
      `/portfolios/${portfolioId}/holdings/${symbol}/price`,
      { current_price: newPrice }
    );
    return response.data;
  },

  // Get comprehensive metrics
  getMetrics: async (portfolioId: string): Promise<PortfolioMetrics> => {
    const response = await api.get<PortfolioMetrics>(
      `/portfolios/${portfolioId}/analysis/metrics`
    );
    return response.data;
  },

  // Get price/value history for a holding
  // If start_date/end_date not provided, backend automatically uses transaction period
  getHoldingHistory: async (
    portfolioId: string,
    symbol: string,
    params?: {
      start_date?: string;
      end_date?: string;
      frequency?: 'daily' | 'weekly' | 'monthly';
    }
  ): Promise<PriceHistoryResponse> => {
    const response = await api.get<PriceHistoryResponse>(
      `/portfolios/${portfolioId}/holdings/${symbol}/history`,
      { params }
    );
    return response.data;
  },

  // Generate AI insights
  generateInsights: async (portfolioId: string): Promise<AIInsightResponse> => {
    const response = await api.post<AIInsightResponse>('/ai/insights', {
      portfolio_id: portfolioId,
    });
    return response.data;
  },

  // Portfolio timeline: cumulative invested vs total value
  getPortfolioTimeline: async (
    portfolioId: string,
    params?: { start_date?: string; end_date?: string }
  ): Promise<PortfolioTimelineResponse> => {
    const response = await api.get<PortfolioTimelineResponse>(
      `/portfolios/${portfolioId}/timeline`,
      { params }
    );
    return response.data;
  },
};

export default api;
