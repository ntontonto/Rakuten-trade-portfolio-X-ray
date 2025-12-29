import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface CumulativeStrategyData {
  month: string;
  core_value: number;
  satellite_value: number;
}

interface CumulativeStrategyBackendData {
  months: string[];
  core: number[];
  satellite: number[];
}

interface CumulativeStrategyChartProps {
  data: CumulativeStrategyData[] | CumulativeStrategyBackendData;
}

export default function CumulativeStrategyChart({ data }: CumulativeStrategyChartProps) {
  const formatCurrency = (value: number) => {
    return `¥${Math.floor(value).toLocaleString()}`;
  };

  // Convert backend object format to array format for the chart
  const chartData: CumulativeStrategyData[] = Array.isArray(data)
    ? data
    : (() => {
        const backendData = data as CumulativeStrategyBackendData;
        const months = backendData.months || [];
        const core = backendData.core || [];
        const satellite = backendData.satellite || [];
        
        return months.map((month, index) => ({
          month,
          core_value: core[index] || 0,
          satellite_value: satellite[index] || 0,
        }));
      })();

  return (
    <div className="chart-card">
      <h3 className="text-sm font-bold text-slate-700 mb-3">
        Core / Satellite 累積推移
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis tickFormatter={formatCurrency} />
          <Tooltip formatter={(value: number | undefined) => formatCurrency(value ?? 0)} />
          <Legend />
          <Area
            type="monotone"
            dataKey="core_value"
            name="Core"
            stackId="1"
            stroke="#6366f1"
            fill="#6366f1"
            fillOpacity={0.6}
          />
          <Area
            type="monotone"
            dataKey="satellite_value"
            name="Satellite"
            stackId="1"
            stroke="#ec4899"
            fill="#ec4899"
            fillOpacity={0.6}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
