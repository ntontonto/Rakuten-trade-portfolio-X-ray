import { useEffect, useMemo, useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  LineChart,
  Line,
} from 'recharts';
import { portfolioAPI } from '../../services/api';
import type {
  Holding,
  PriceHistoryPoint,
  PriceHistoryResponse,
  InvestmentTimelinePoint,
  InvestmentTimelineResponse,
} from '../../types';

interface AssetDetailProps {
  holding: Holding;
  portfolioId: string;
  onClose: () => void;
}

type RangeKey = '3M' | '6M' | '1Y' | 'MAX';
type FrequencyKey = 'daily' | 'weekly' | 'monthly';

const RANGE_OPTIONS: Record<RangeKey, number | null> = {
  '3M': 90,
  '6M': 180,
  '1Y': 365,
  MAX: null, // Use full transaction period
};

export default function AssetDetail({ holding, portfolioId, onClose }: AssetDetailProps) {
  const [range, setRange] = useState<RangeKey>('MAX'); // Default to transaction period
  const [frequency, setFrequency] = useState<FrequencyKey>('daily');
  const [history, setHistory] = useState<PriceHistoryResponse | null>(null);
  const [timeline, setTimeline] = useState<InvestmentTimelineResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const days = RANGE_OPTIONS[range];

        // For MAX range, don't pass any dates - let backend use transaction period
        const params: any = { frequency };

        if (days !== null) {
          // For specific ranges (3M, 6M, 1Y), calculate dates
          const end = new Date();
          const start = new Date(end.getTime() - days * 24 * 60 * 60 * 1000);
          params.start_date = start.toISOString().slice(0, 10);
          params.end_date = end.toISOString().slice(0, 10);
        }
        // else: MAX range - backend will use first_purchase_date to today

        const [historyRes, timelineRes] = await Promise.all([
          portfolioAPI.getHoldingHistory(portfolioId, holding.symbol, params),
          portfolioAPI.getInvestmentTimeline(portfolioId, holding.symbol, params),
        ]);
        setHistory(historyRes);
        setTimeline(timelineRes);
      } catch (e: any) {
        setError(e.response?.data?.detail || e.message || 'Failed to load history');
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [holding.symbol, portfolioId, range, frequency]);

  const chartData = useMemo(() => {
    if (!history) return [];
    return history.points.map((p: PriceHistoryPoint) => ({
      date: p.date,
      price: p.price_jpy ?? p.price_raw,
    }));
  }, [history]);

  const latestPoint = useMemo(() => {
    if (!history || history.points.length === 0) return null;
    const last = history.points[history.points.length - 1];
    return {
      price: last.price_jpy ?? last.price_raw,
      date: last.date,
    };
  }, [history]);

  const timelineData = useMemo(() => {
    if (!timeline) return [];
    return timeline.points.map((p: InvestmentTimelinePoint) => ({
      date: p.date,
      invested: p.invested_cumulative_jpy,
      value: p.value_jpy,
    }));
  }, [timeline]);

  return (
    <div className="fixed inset-0 bg-black/30 flex items-end sm:items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl mx-4 overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <div>
            <div className="text-sm text-slate-500">{holding.symbol}</div>
            <div className="text-lg font-semibold text-slate-800">{holding.name}</div>
          </div>
          <div className="flex items-center gap-2">
            {history && (
              <span className="px-2 py-1 text-xs rounded bg-slate-100 text-slate-600 border border-slate-200">
                Source: {history.source}
              </span>
            )}
            <button
              onClick={onClose}
              className="text-slate-500 hover:text-slate-800 text-sm font-medium"
            >
              Close
            </button>
          </div>
        </div>

        <div className="px-6 py-4 space-y-4">
          {/* Time Range Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium mr-1">Range:</span>
            {(Object.keys(RANGE_OPTIONS) as RangeKey[]).map((key) => (
              <button
                key={key}
                onClick={() => setRange(key)}
                className={`px-3 py-1.5 text-sm rounded border ${
                  range === key
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
                }`}
              >
                {key}
              </button>
            ))}
          </div>

          {/* Frequency Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium mr-1">Frequency:</span>
            {(['daily', 'weekly', 'monthly'] as FrequencyKey[]).map((freq) => (
              <button
                key={freq}
                onClick={() => setFrequency(freq)}
                className={`px-3 py-1.5 text-sm rounded border capitalize ${
                  frequency === freq
                    ? 'bg-emerald-600 text-white border-emerald-600'
                    : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
                }`}
              >
                {freq}
              </button>
            ))}
          </div>

          {loading && <div className="text-sm text-slate-500">Loading history…</div>}
          {error && <div className="text-sm text-red-600">Error: {error}</div>}

          {!loading && !error && history && history.points.length === 0 && (
            <div className="text-sm text-slate-500">No history available for this asset.</div>
          )}

          {!loading && !error && history && history.points.length > 0 && (
            <div className="space-y-3">
              {latestPoint && (
                <div className="flex items-center gap-4 text-sm text-slate-700">
                  <div>
                    Latest Price:{' '}
                    <span className="font-semibold text-slate-900">
                      ¥{latestPoint.price?.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="text-slate-400">as of {latestPoint.date}</div>
                </div>
              )}

              <div className="h-72">
                <ResponsiveContainer>
                  <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#2563eb" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip
                      formatter={(value: number) =>
                        `¥${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
                      }
                    />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="price"
                      stroke="#2563eb"
                      fill="url(#priceFill)"
                      name="Price (JPY)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {timelineData.length > 0 && (
                <div className="h-72">
                  <ResponsiveContainer>
                    <LineChart data={timelineData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip
                        formatter={(value: number) =>
                          `¥${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                        }
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="invested"
                        stroke="#0ea5e9"
                        dot={false}
                        name="累計投資額"
                        strokeWidth={2}
                      />
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#22c55e"
                        dot={false}
                        name="評価額"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
