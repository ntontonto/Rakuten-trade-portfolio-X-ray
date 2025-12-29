import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface MonthlyFlowData {
  month: string;
  invested: number;
  withdrawn: number;
}

interface MonthlyFlowBackendData {
  [month: string]: {
    core: number;
    satellite: number;
  };
}

interface MonthlyFlowChartProps {
  data: MonthlyFlowData[] | MonthlyFlowBackendData;
}

export default function MonthlyFlowChart({ data }: MonthlyFlowChartProps) {
  const formatCurrency = (value: number) => {
    return `¥${Math.floor(Math.abs(value)).toLocaleString()}`;
  };

  // Convert backend object format to array format for the chart
  const chartData: MonthlyFlowData[] = Array.isArray(data)
    ? data
    : Object.entries(data || {})
        .map(([month, values]) => ({
          month,
          invested: (values.core || 0) + (values.satellite || 0),
          withdrawn: 0, // Backend doesn't currently track withdrawals separately
        }))
        .sort((a, b) => a.month.localeCompare(b.month));

  return (
    <div className="chart-card">
      <h3 className="text-sm font-bold text-slate-700 mb-3">
        月次投資フロー
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis tickFormatter={formatCurrency} />
          <Tooltip formatter={(value: number | undefined) => formatCurrency(value ?? 0)} />
          <Legend />
          <Bar dataKey="invested" name="投資額" fill="#10b981" stackId="a" />
          <Bar dataKey="withdrawn" name="売却額" fill="#ef4444" stackId="a" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
