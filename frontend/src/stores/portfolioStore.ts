// Zustand store for portfolio state management

import { create } from 'zustand';
import type { Portfolio, PortfolioSummary, Holding, PortfolioMetrics } from '../types';

interface PortfolioState {
  // State
  currentPortfolio: Portfolio | null;
  summary: PortfolioSummary | null;
  holdings: Holding[];
  metrics: PortfolioMetrics | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setCurrentPortfolio: (portfolio: Portfolio | null) => void;
  setSummary: (summary: PortfolioSummary | null) => void;
  setHoldings: (holdings: Holding[]) => void;
  setMetrics: (metrics: PortfolioMetrics | null) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const usePortfolioStore = create<PortfolioState>((set) => ({
  // Initial state
  currentPortfolio: null,
  summary: null,
  holdings: [],
  metrics: null,
  isLoading: false,
  error: null,

  // Actions
  setCurrentPortfolio: (portfolio) => set({ currentPortfolio: portfolio }),
  setSummary: (summary) => set({ summary }),
  setHoldings: (holdings) => set({ holdings }),
  setMetrics: (metrics) => set({ metrics }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  reset: () =>
    set({
      currentPortfolio: null,
      summary: null,
      holdings: [],
      metrics: null,
      isLoading: false,
      error: null,
    }),
}));
