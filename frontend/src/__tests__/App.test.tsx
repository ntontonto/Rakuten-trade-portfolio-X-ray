import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { portfolioAPI } from '../services/api';
import { usePortfolioStore } from '../stores/portfolioStore';

// Mock heavy chart components to simple placeholders
vi.mock('../components/charts/AssetAllocationChart', () => ({ default: () => <div data-testid="asset-chart" /> }));
vi.mock('../components/charts/StrategyChart', () => ({ default: () => <div data-testid="strategy-chart" /> }));
vi.mock('../components/charts/XIRRBarChart', () => ({ default: () => <div data-testid="xirr-chart" /> }));
vi.mock('../components/charts/MonthlyFlowChart', () => ({ default: () => <div data-testid="flow-chart" /> }));
vi.mock('../components/charts/RealizedPLChart', () => ({ default: () => <div data-testid="pl-chart" /> }));
vi.mock('../components/charts/TopPerformersChart', () => ({ default: () => <div data-testid="top-chart" /> }));
vi.mock('../components/charts/CumulativeStrategyChart', () => ({ default: () => <div data-testid="cumulative-chart" /> }));
vi.mock('../components/charts/WinRateChart', () => ({ default: () => <div data-testid="winrate-chart" /> }));
vi.mock('../components/charts/ScatterChart', () => ({ default: () => <div data-testid="scatter-chart" /> }));
vi.mock('../components/kpi/XIRRGauge', () => ({ default: ({ xirr }: { xirr: number }) => <div data-testid="xirr-gauge">{xirr}</div> }));
vi.mock('../components/kpi/MetricsGrid', () => ({ default: () => <div data-testid="metrics-grid" /> }));
vi.mock('../components/ai/AIInsightPanel', () => ({ default: () => <div data-testid="ai-panel" /> }));

vi.mock('../services/api', () => ({
  portfolioAPI: {
    uploadCSV: vi.fn(),
    getHoldings: vi.fn(),
    getMetrics: vi.fn(),
  },
}));

describe('App integration', () => {
  const mockUpload = portfolioAPI as unknown as {
    uploadCSV: ReturnType<typeof vi.fn>;
    getHoldings: ReturnType<typeof vi.fn>;
    getMetrics: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    usePortfolioStore.getState().reset();
    vi.clearAllMocks();
    mockUpload.uploadCSV.mockResolvedValue({
      portfolio_id: 'p1',
      summary: {
        portfolio_id: 'p1',
        total_xirr: 0.12,
        total_current_value: 100000,
        total_invested: 80000,
        total_unrealized_pl: 20000,
        total_realized_pl: 0,
        return_rate: 0.25,
        holdings_count: 1,
      },
    });
    mockUpload.getHoldings.mockResolvedValue([
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
    ]);
    mockUpload.getMetrics.mockResolvedValue({
      total_xirr: 0.12,
      total_current_value: 100000,
      total_invested: 80000,
      total_unrealized_pl: 20000,
      total_realized_pl: 0,
      return_rate: 0.25,
      allocation_by_class: [{ asset_class: 'Equity', percentage: 1, total_value: 100000 }],
      allocation_by_strategy: [{ strategy: 'Core', percentage: 1, total_value: 100000 }],
      xirr_by_class: [{ asset_class: 'Equity', xirr: 0.12 }],
      monthly_flow: [{ month: '2023-01', invested: 10000, withdrawn: 0 }],
      realized_pl_by_class: { Equity: 0 }, // Changed to object format
      top_performers: [{ symbol: 'VTI', name: 'Vanguard Total Stock', xirr: 0.2, current_value: 100000 }],
      cumulative_strategy: [{ month: '2023-01', core_value: 10000, satellite_value: 0 }],
      win_rate: [{ label: '利益', count: 1, percentage: 1 }],
      scatter_data: [{ symbol: 'VTI', name: 'Vanguard Total Stock', holding_days: 30, xirr: 0.2, current_value: 100000, asset_class: 'Equity' }],
    });
  });

  it('uploads files and shows dashboard data', async () => {
    render(<App />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['csvcontent'], 'portfolio.csv', { type: 'text/csv' });

    await userEvent.upload(fileInput, file);

    await waitFor(() => {
      expect(mockUpload.uploadCSV).toHaveBeenCalled();
    });

    // Dashboard should render KPI components
    expect(await screen.findByTestId('xirr-gauge')).toHaveTextContent('0.12');
    expect(screen.getByTestId('metrics-grid')).toBeInTheDocument();
  });
});
