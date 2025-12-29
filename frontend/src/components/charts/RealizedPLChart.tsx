import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface RealizedPLData {
  asset_class: string;
  realized_pl: number;
}

interface RealizedPLChartProps {
  data: Record<string, number> | RealizedPLData[];
}

const COLORS = {
  Equity: '#3b82f6',
  Bond: '#10b981',
  REIT: '#f59e0b',
  Commodity: '#ef4444',
  Cash: '#6b7280',
};

export default function RealizedPLChart({ data }: RealizedPLChartProps) {
  const formatCurrency = (value: number) => {
    return `¥${Math.floor(value).toLocaleString()}`;
  };

  // Convert data to array format if it's an object
  const chartData: RealizedPLData[] = Array.isArray(data)
    ? data
    : Object.entries(data || {}).map(([asset_class, realized_pl]) => ({
        asset_class,
        realized_pl,
      }));

  return (
    <div className="chart-card">
      <h3 className="text-sm font-bold text-slate-700 mb-3">
        資産クラス別 確定損益
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="asset_class" />
          <YAxis tickFormatter={formatCurrency} />
          <Tooltip formatter={(value: number | undefined) => formatCurrency(value ?? 0)} />
          <Bar dataKey="realized_pl" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[entry.asset_class as keyof typeof COLORS] || '#94a3b8'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
