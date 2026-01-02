import { useEffect, useMemo, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { portfolioAPI } from '../../services/api';
import type { PortfolioTimelinePoint, PortfolioTimelineResponse } from '../../types';
import { usePortfolioStore } from '../../stores/portfolioStore';

type RangeKey = '3M' | '6M' | '1Y' | 'MAX';

const RANGE_OPTIONS: Record<RangeKey, number | null> = {
  '3M': 90,
  '6M': 180,
  '1Y': 365,
  MAX: null,
};

export default function PortfolioTimelineChart() {
  const { currentPortfolio } = usePortfolioStore();
  const [range, setRange] = useState<RangeKey>('1Y');
  const [data, setData] = useState<PortfolioTimelineResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!currentPortfolio) return;
      setLoading(true);
      setError(null);
      try {
        const days = RANGE_OPTIONS[range];
        const end = new Date();
        const start =
          days !== null ? new Date(end.getTime() - days * 24 * 60 * 60 * 1000) : null;
        const response = await portfolioAPI.getPortfolioTimeline(currentPortfolio.id, {
          start_date: start ? start.toISOString().slice(0, 10) : undefined,
          end_date: end.toISOString().slice(0, 10),
        });
        setData(response);
      } catch (e: any) {
        setError(e.response?.data?.detail || e.message || 'Failed to load timeline');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [currentPortfolio, range]);

  const chartData = useMemo(() => data?.points ?? [], [data]);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 h-full">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-sm font-bold text-slate-700">累積投資額 vs 評価額 (日次)</h4>
          <p className="text-xs text-slate-500">日次での総投資額とポートフォリオ評価額の推移</p>
        </div>
        <div className="flex items-center gap-2">
          {(Object.keys(RANGE_OPTIONS) as RangeKey[]).map((key) => (
            <button
              key={key}
              onClick={() => setRange(key)}
              className={`px-2.5 py-1 text-xs rounded border ${
                range === key
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
              }`}
            >
              {key}
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="text-sm text-slate-500">Loading timeline…</div>}
      {error && <div className="text-sm text-red-600">Error: {error}</div>}
      {!loading && !error && chartData.length === 0 && (
        <div className="text-sm text-slate-500">No timeline data.</div>
      )}

      {!loading && !error && chartData.length > 0 && (
        <div className="h-72">
          <ResponsiveContainer>
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value: number) =>
                  `¥${Math.round(value).toLocaleString(undefined, {
                    maximumFractionDigits: 0,
                  })}`
                }
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="invested_cumulative_jpy"
                stroke="#2563eb"
                name="累積投資額 (¥)"
                dot={false}
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="total_value_jpy"
                stroke="#10b981"
                name="評価額 (¥)"
                dot={false}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
