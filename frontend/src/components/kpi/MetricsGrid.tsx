import { Wallet, TrendingUp, PiggyBank } from 'lucide-react';
import type { PortfolioSummary } from '../../types';

interface MetricsGridProps {
  summary: PortfolioSummary;
}

export default function MetricsGrid({ summary }: MetricsGridProps) {
  const formatCurrency = (value: number) => {
    return `¥${Math.floor(value).toLocaleString()}`;
  };

  const formatPercent = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${(value * 100).toFixed(1)}%`;
  };

  return (
    <div className="grid grid-cols-3 gap-4 h-64">
      {/* Current Value */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-center relative overflow-hidden group">
        <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
          <Wallet className="w-16 h-16 text-blue-600" />
        </div>
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">
          現在の資産評価額
        </p>
        <h3 className="text-2xl font-extrabold text-slate-800 mt-1">
          {formatCurrency(summary.total_current_value)}
        </h3>
        <p className="text-xs text-slate-500 mt-2">
          累計投資額: {formatCurrency(summary.total_invested)}
        </p>
      </div>

      {/* Unrealized P&L */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-center relative overflow-hidden group">
        <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
          <TrendingUp className="w-16 h-16 text-emerald-600" />
        </div>
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">
          含み損益 (評価益)
        </p>
        <h3
          className={`text-2xl font-extrabold mt-1 ${
            summary.total_unrealized_pl >= 0 ? 'text-emerald-600' : 'text-red-600'
          }`}
        >
          {formatCurrency(summary.total_unrealized_pl)}
        </h3>
        <div className="flex items-center gap-2 mt-2">
          <span
            className={`text-xs font-bold px-2 py-0.5 rounded-full ${
              summary.return_rate >= 0
                ? 'bg-emerald-100 text-emerald-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {formatPercent(summary.return_rate)}
          </span>
        </div>
      </div>

      {/* Realized P&L */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-center relative overflow-hidden group">
        <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
          <PiggyBank className="w-16 h-16 text-orange-600" />
        </div>
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">
          確定利益 (実現損益)
        </p>
        <h3 className="text-2xl font-extrabold text-orange-600 mt-1">
          {formatCurrency(summary.total_realized_pl)}
        </h3>
        <p className="text-xs text-slate-500 mt-2">配当・分配金込(推定)</p>
      </div>
    </div>
  );
}
