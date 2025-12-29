import {
  ScatterChart as RechartsScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ZAxis,
} from 'recharts';

interface ScatterData {
  symbol: string;
  name: string;
  holding_days: number;
  xirr: number;
  current_value: number;
  asset_class: string;
}

interface ScatterChartProps {
  data: ScatterData[];
}

const COLORS = {
  Equity: '#3b82f6',
  Bond: '#10b981',
  REIT: '#f59e0b',
  Commodity: '#ef4444',
  Cash: '#6b7280',
};

const formatPercent = (value: number) => {
  return `${(value * 100).toFixed(1)}%`;
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: ScatterData }>;
}

const CustomTooltip = ({ active, payload }: CustomTooltipProps) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-3 border border-slate-200 rounded shadow-lg">
        <p className="font-bold text-slate-700">{data.name}</p>
        <p className="text-xs text-slate-500">{data.symbol}</p>
        <p className="text-sm mt-1">
          保有期間: <span className="font-medium">{data.holding_days}日</span>
        </p>
        <p className="text-sm">
          XIRR: <span className="font-medium">{formatPercent(data.xirr)}</span>
        </p>
        <p className="text-sm">
          評価額: <span className="font-medium">
            ¥{Math.floor(data.current_value).toLocaleString()}
          </span>
        </p>
      </div>
    );
  }
  return null;
};

// Custom shape function to color dots by asset class
interface CustomDotProps {
  cx?: number;
  cy?: number;
  payload?: ScatterData;
}

const CustomDot = (props: CustomDotProps) => {
  const { cx, cy, payload } = props;
  if (!cx || !cy || !payload) return null;
  const color = COLORS[payload.asset_class as keyof typeof COLORS] || '#94a3b8';
  return (
    <circle
      cx={cx}
      cy={cy}
      r={8}
      fill={color}
      fillOpacity={0.6}
      stroke={color}
      strokeWidth={1}
    />
  );
};

export default function ScatterChart({ data }: ScatterChartProps) {
  return (
    <div className="chart-card">
      <h3 className="text-sm font-bold text-slate-700 mb-3">
        保有期間 vs XIRR (バブルサイズ=評価額)
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsScatterChart
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            type="number"
            dataKey="holding_days"
            name="保有期間"
            unit="日"
          />
          <YAxis
            type="number"
            dataKey="xirr"
            name="XIRR"
            tickFormatter={formatPercent}
          />
          <ZAxis
            type="number"
            dataKey="current_value"
            range={[50, 400]}
            name="評価額"
          />
          <Tooltip content={<CustomTooltip />} />
          <Scatter
            name="保有銘柄"
            data={data}
            fill="#3b82f6"
            shape={<CustomDot />}
          />
        </RechartsScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
