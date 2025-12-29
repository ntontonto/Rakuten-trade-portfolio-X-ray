import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HoldingsTable from '../components/table/HoldingsTable';
import { usePortfolioStore } from '../stores/portfolioStore';
import { portfolioAPI } from '../services/api';

vi.mock('../services/api', () => ({
  portfolioAPI: {
    updateHoldingPrice: vi.fn(),
    getHoldings: vi.fn().mockResolvedValue([
      {
        id: '1',
        portfolio_id: 'p1',
        symbol: 'VTI',
        name: 'Vanguard Total Stock',
        quantity: 1,
        current_price: 120,
        current_value: 120,
        average_cost: 100,
        invested_amount: 100,
        unrealized_pl: 20,
        asset_class: 'Equity',
        strategy: 'Core',
        is_price_auto_updated: false,
      },
    ]),
  },
}));

const mockAPI = portfolioAPI as unknown as {
  updateHoldingPrice: ReturnType<typeof vi.fn>;
  getHoldings: ReturnType<typeof vi.fn>;
};

describe('HoldingsTable', () => {
  beforeEach(() => {
    vi.spyOn(window, 'alert').mockImplementation(() => {});
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

  it('filters holdings by search term', async () => {
    const holdings = [
      {
        id: '1',
        portfolio_id: 'p1',
        symbol: 'VTI',
        name: 'Vanguard Total Stock',
        quantity: 10,
        current_price: 120,
        current_value: 1200,
        average_cost: 100,
        invested_amount: 1000,
        unrealized_pl: 200,
        asset_class: 'Equity',
        strategy: 'Core',
        is_price_auto_updated: false,
      },
      {
        id: '2',
        portfolio_id: 'p1',
        symbol: 'BND',
        name: 'Total Bond',
        quantity: 5,
        current_price: 80,
        current_value: 400,
        average_cost: 90,
        invested_amount: 450,
        unrealized_pl: -50,
        asset_class: 'Bond',
        strategy: 'Satellite',
        is_price_auto_updated: false,
      },
    ];

    render(<HoldingsTable holdings={holdings} />);

    expect(screen.getByText('Vanguard Total Stock')).toBeInTheDocument();
    expect(screen.getByText('Total Bond')).toBeInTheDocument();

    const search = screen.getByPlaceholderText('銘柄名で検索...');
    userEvent.type(search, 'VTI');

    await waitFor(() => {
      expect(screen.queryByText('Total Bond')).not.toBeInTheDocument();
    });
    expect(screen.getByText('Vanguard Total Stock')).toBeInTheDocument();
  });

  it('saves edited price and refreshes holdings', async () => {
    const holdings = [
      {
        id: '1',
        portfolio_id: 'p1',
        symbol: 'VTI',
        name: 'Vanguard Total Stock',
        quantity: 10,
        current_price: 120,
        current_value: 1200,
        average_cost: 100,
        invested_amount: 1000,
        unrealized_pl: 200,
        asset_class: 'Equity',
        strategy: 'Core',
        is_price_auto_updated: false,
      },
    ];

    render(<HoldingsTable holdings={holdings} />);

    const editButton = screen.getByTitle(/手動入力が必要/);
    await userEvent.click(editButton);

    const input = await screen.findByRole('spinbutton');
    await userEvent.clear(input);
    await userEvent.type(input, '150');
    fireEvent.blur(input);

    await waitFor(() => {
      expect(mockAPI.updateHoldingPrice).toHaveBeenCalledWith('p1', 'VTI', 150);
    });
    expect(mockAPI.getHoldings).toHaveBeenCalledWith('p1');
  });
});
