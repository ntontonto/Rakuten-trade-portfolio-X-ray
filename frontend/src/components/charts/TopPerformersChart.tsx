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

interface TopPerformerData {
  symbol: string;
  name: string;
  xirr: number;
}

interface TopPerformersChartProps {
  data: TopPerformerData[];
}

export default function TopPerformersChart({ data }: TopPerformersChartProps) {
  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const getColor = (xirr: number) => {
    if (xirr >= 0.2) return '#10b981'; // Green for >20%
    if (xirr >= 0.1) return '#3b82f6'; // Blue for 10-20%
    if (xirr >= 0) return '#6b7280'; // Gray for 0-10%
    return '#ef4444'; // Red for negative
  };

  return (
    <div className="chart-card">
      <h3 className="text-sm font-bold text-slate-700 mb-3">
        XIRR Top 5 パフォーマー
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 120, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" tickFormatter={formatPercent} />
          <YAxis
            dataKey="symbol"
            type="category"
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            formatter={(value: number) => formatPercent(value)}
            labelFormatter={(label) => {
              const item = data.find((d) => d.symbol === label);
              return item ? `${item.name} (${item.symbol})` : label;
            }}
          />
          <Bar dataKey="xirr" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.xirr)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
