import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface WinRateData {
  label: string;
  count: number;
  percentage: number;
  [key: string]: string | number; // Index signature for recharts compatibility
}

interface WinRateBackendData {
  total: number;
  winning: number;
  rate: number;
}

interface WinRateChartProps {
  data: WinRateBackendData | WinRateData[];
}

const COLORS = {
  '利益': '#10b981',
  '損失': '#ef4444',
  '±0': '#6b7280',
};

export default function WinRateChart({ data }: WinRateChartProps) {
  // Convert backend object format to array format for the chart
  const chartData: WinRateData[] = Array.isArray(data)
    ? data
    : (() => {
        const backendData = data as WinRateBackendData;
        const winning = backendData.winning || 0;
        const losing = (backendData.total || 0) - winning;
        return [
          { label: '利益', count: winning, percentage: backendData.rate || 0 },
          { label: '損失', count: losing, percentage: 1 - (backendData.rate || 0) },
        ].filter(item => item.count > 0);
      })();

  return (
    <div className="chart-card">
      <h3 className="text-sm font-bold text-slate-700 mb-3">
        決済ポジション 勝率
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            dataKey="count"
            nameKey="label"
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={80}
            label={(props) => {
              const entry = props.payload as WinRateData;
              return `${entry.label} ${(entry.percentage * 100).toFixed(1)}%`;
            }}
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[entry.label as keyof typeof COLORS] || '#94a3b8'}
              />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number | undefined, name: string | undefined) => [
              `${value ?? 0}件`,
              name ?? '',
            ]}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
