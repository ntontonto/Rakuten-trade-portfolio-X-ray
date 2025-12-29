import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface AllocationData {
  labels: string[];
  values: number[];
  colors: string[];
}

interface AssetAllocationChartProps {
  data: AllocationData;
}

export default function AssetAllocationChart({ data }: AssetAllocationChartProps) {
  const formatCurrency = (value: number) => {
    return `¥${Math.floor(value).toLocaleString()}`;
  };

  // Safety check for data
  if (!data || !data.labels || !data.values || !Array.isArray(data.labels) || !Array.isArray(data.values)) {
    return (
      <div className="chart-card">
        <h3 className="text-sm font-bold text-slate-700 mb-3">
          資産クラス別 配分
        </h3>
        <div className="flex items-center justify-center h-full">
          <p className="text-slate-400 text-sm">データがありません</p>
        </div>
      </div>
    );
  }

  // Transform backend data to chart format
  const total = data.values.reduce((sum, val) => sum + val, 0);
  const chartData = data.labels.map((label, index) => ({
    name: label,
    value: data.values[index],
    percentage: total > 0 ? (data.values[index] / total) * 100 : 0,
  }));

  return (
    <div className="chart-card">
      <h3 className="text-sm font-bold text-slate-700 mb-3">
        資産クラス別 配分
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={80}
            label={({ name, percentage }) =>
              `${name} ${percentage.toFixed(1)}%`
            }
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={data.colors[index] || '#94a3b8'}
              />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => formatCurrency(value)}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
