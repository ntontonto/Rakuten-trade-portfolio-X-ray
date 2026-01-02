// TypeScript type definitions for Portfolio X-Ray

export interface Portfolio {
  id: string;
  name: string;
  created_at: string;
  updated_at?: string;
  metadata?: Record<string, unknown>;
}

export interface Transaction {
  id: string;
  portfolio_id: string;
  transaction_date: string;
  symbol: string;
  name: string;
  side: 'BUY' | 'SELL' | 'OTHER';
  transaction_type?: string;
  quantity: number;
  amount_jpy: number;
  market: 'US' | 'JP' | 'INVST';
  asset_class?: 'Equity' | 'Bond' | 'REIT' | 'Commodity';
}

export interface Holding {
  id: string;
  portfolio_id: string;
  symbol: string;
  name: string;
  quantity: number;
  average_cost?: number;
  current_price?: number;
  current_value?: number;
  invested_amount?: number;
  points_invested?: number;
  invested_amount_with_points?: number;
  unrealized_pl?: number;
  realized_pl?: number;
  xirr?: number;
  asset_class?: 'Equity' | 'Bond' | 'REIT' | 'Commodity';
  strategy?: 'Core' | 'Satellite';
  market?: 'US' | 'JP' | 'INVST';
  first_purchase_date?: string;
  last_transaction_date?: string;
  holding_days?: number;
  is_price_auto_updated: boolean;
}

export interface PortfolioSummary {
  portfolio_id: string;
  total_xirr: number;
  total_current_value: number;
  total_invested: number;
  points_invested: number;
  total_invested_with_points: number;
  total_unrealized_pl: number;
  total_realized_pl: number;
  return_rate: number;
  holdings_count: number;
  last_calculated_at?: string;
}

export interface AllocationData {
  labels: string[];
  values: number[];
  colors: string[];
}

export interface StrategyAllocation {
  labels: string[];
  values: number[];
  colors: string[];
}

export interface PortfolioMetrics {
  total_xirr: number;
  total_current_value: number;
  total_invested: number;
  points_invested: number;
  total_invested_with_points: number;
  total_unrealized_pl: number;
  total_realized_pl: number;
  return_rate: number;
  allocation_by_class: AllocationData;
  allocation_by_strategy: StrategyAllocation;
  xirr_by_class: Record<string, number>;
  monthly_flow: Record<string, { core: number; satellite: number }>;
  top_performers: Array<{ symbol: string; name: string; xirr: number; current_value: number }>;
  realized_pl_by_class: Record<string, number>;
  cumulative_strategy: { months: string[]; core: number[]; satellite: number[] };
  win_rate: { total: number; winning: number; rate: number };
  scatter_data: Array<{
    symbol: string;
    name: string;
    holding_days: number;
    xirr: number;
    current_value: number;
    asset_class?: string;
    strategy?: string;
  }>;
}

export interface PriceHistoryPoint {
  date: string;
  price_jpy?: number;
  price_raw: number;
  fx_rate?: number;
  quantity?: number;
  value_jpy?: number;
}

export interface PriceHistoryResponse {
  source: string;
  currency: string;
  points: PriceHistoryPoint[];
}

export interface PortfolioTimelinePoint {
  date: string;
  invested_cumulative_jpy: number;
  total_value_jpy: number;
}

export interface PortfolioTimelineResponse {
  points: PortfolioTimelinePoint[];
}

export interface AIInsightResponse {
  status: 'success' | 'error' | string;
  report: string;
  generated_at: string;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  portfolio_id: string;
  files_processed: Array<{ filename: string; type: string }>;
  transactions_imported: number;
  holdings_created: number;
  summary: PortfolioSummary;
}
