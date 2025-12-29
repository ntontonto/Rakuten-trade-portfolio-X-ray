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

interface XIRRBarChartProps {
  data: Record<string, number>; // Backend returns { "Equity": 0.15, "Bond": 0.05 }
}

const COLORS: Record<string, string> = {
  Equity: '#3b82f6',
  Bond: '#10b981',
  REIT: '#f59e0b',
  Commodity: '#ef4444',
  Cash: '#6b7280',
};

export default function XIRRBarChart({ data }: XIRRBarChartProps) {
  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  // Safety check for data
  if (!data || typeof data !== 'object' || Object.keys(data).length === 0) {
    return (
      <div className="chart-card">
        <h3 className="text-sm font-bold text-slate-700 mb-3">
          資産クラス別 XIRR
        </h3>
        <div className="flex items-center justify-center h-full">
          <p className="text-slate-400 text-sm">データがありません</p>
        </div>
      </div>
    );
  }

  // Transform backend dict to chart array
  const chartData = Object.entries(data).map(([asset_class, xirr]) => ({
    asset_class,
    xirr,
  }));

  return (
    <div className="chart-card">
      <h3 className="text-sm font-bold text-slate-700 mb-3">
        資産クラス別 XIRR
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" tickFormatter={formatPercent} />
          <YAxis dataKey="asset_class" type="category" />
          <Tooltip formatter={(value: number) => formatPercent(value)} />
          <Bar dataKey="xirr" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[entry.asset_class] || '#94a3b8'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
