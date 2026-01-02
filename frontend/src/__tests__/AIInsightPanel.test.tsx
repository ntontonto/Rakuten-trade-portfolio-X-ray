import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AIInsightPanel from '../components/ai/AIInsightPanel';
import { usePortfolioStore } from '../stores/portfolioStore';
import { portfolioAPI } from '../services/api';

vi.mock('../services/api', () => ({
  portfolioAPI: {
    generateInsights: vi.fn().mockResolvedValue({
      status: 'success',
      report: '## Test Insight\n- Point A\n- Point B',
      generated_at: '2024-01-01T00:00:00Z',
    }),
  },
}));

describe('AIInsightPanel', () => {
  beforeEach(() => {
    usePortfolioStore.setState({
      currentPortfolio: { id: 'p1', name: 'Main', created_at: '' },
      summary: null,
      holdings: [],
      metrics: null,
      isLoading: false,
      error: null,
      setCurrentPortfolio: (portfolio) => usePortfolioStore.setState({ currentPortfolio: portfolio }),
      setSummary: (summary) => usePortfolioStore.setState({ summary }),
      setHoldings: (holdings) => usePortfolioStore.setState({ holdings }),
      setMetrics: (metrics) => usePortfolioStore.setState({ metrics }),
      setLoading: (isLoading) => usePortfolioStore.setState({ isLoading }),
      setError: (error) => usePortfolioStore.setState({ error }),
      reset: () => usePortfolioStore.setState({
        currentPortfolio: null,
        summary: null,
        holdings: [],
        metrics: null,
        isLoading: false,
        error: null,
      }),
    });
    vi.clearAllMocks();
  });

  it('fetches and renders AI insight markdown', async () => {
    render(<AIInsightPanel />);

    const button = screen.getByRole('button', { name: /分析を実行/i });
    await userEvent.click(button);

    await waitFor(() => {
      expect(portfolioAPI.generateInsights).toHaveBeenCalledWith('p1');
    });

    expect(await screen.findByText('Test Insight')).toBeInTheDocument();
    expect(screen.getByText('Point A')).toBeInTheDocument();
  });
});
