import { usePortfolioStore } from '../../stores/portfolioStore';
import XIRRGauge from '../kpi/XIRRGauge';
import MetricsGrid from '../kpi/MetricsGrid';
import HoldingsTable from '../table/HoldingsTable';
import AssetAllocationChart from '../charts/AssetAllocationChart';
import StrategyChart from '../charts/StrategyChart';
import XIRRBarChart from '../charts/XIRRBarChart';
import MonthlyFlowChart from '../charts/MonthlyFlowChart';
import RealizedPLChart from '../charts/RealizedPLChart';
import TopPerformersChart from '../charts/TopPerformersChart';
import CumulativeStrategyChart from '../charts/CumulativeStrategyChart';
import WinRateChart from '../charts/WinRateChart';
import ScatterChart from '../charts/ScatterChart';
import AIInsightPanel from '../ai/AIInsightPanel';

export default function Dashboard() {
  const { summary, holdings, metrics, isLoading } = usePortfolioStore();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent mb-4 mx-auto"></div>
          <p className="text-lg font-bold text-slate-700">データ解析中...</p>
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="text-center py-16">
        <p className="text-slate-500">データがありません</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* KPI Section */}
      <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* XIRR Gauge */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 h-64 md:col-span-1">
          <h4 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">
            Portfolio XIRR
          </h4>
          <XIRRGauge xirr={summary.total_xirr} />
        </div>

        {/* Metrics Grid */}
        <div className="md:col-span-3">
          <MetricsGrid summary={summary} />
        </div>
      </section>

      {/* Holdings Table */}
      <section className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50">
          <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            資産シミュレーター (XIRR再計算)
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            ※「現在単価」を修正すると、XIRRおよび資産評価額がリアルタイムで再計算されます。
          </p>
        </div>
        <HoldingsTable holdings={holdings} />
      </section>

      {/* Charts Section */}
      {metrics && (
        <>
          {/* Asset Allocation Charts */}
          <section>
            <h3 className="text-xl font-bold text-slate-800 mb-4">
              資産配分・戦略分析
            </h3>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <AssetAllocationChart data={metrics.allocation_by_class} />
              <StrategyChart data={metrics.allocation_by_strategy} />
              <XIRRBarChart data={metrics.xirr_by_class} />
            </div>
          </section>

          {/* Performance & Flow Charts */}
          <section>
            <h3 className="text-xl font-bold text-slate-800 mb-4">
              パフォーマンス分析
            </h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <MonthlyFlowChart data={metrics.monthly_flow} />
              <RealizedPLChart data={metrics.realized_pl_by_class} />
            </div>
          </section>

          {/* Top Performers & Trends */}
          <section>
            <h3 className="text-xl font-bold text-slate-800 mb-4">
              パフォーマー分析・トレンド
            </h3>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <TopPerformersChart data={metrics.top_performers} />
              <CumulativeStrategyChart data={metrics.cumulative_strategy} />
              <WinRateChart data={metrics.win_rate} />
            </div>
          </section>

          {/* Scatter Chart */}
          <section>
            <h3 className="text-xl font-bold text-slate-800 mb-4">
              保有期間 vs リターン分析
            </h3>
            <div className="grid grid-cols-1">
              <ScatterChart data={metrics.scatter_data} />
            </div>
          </section>
        </>
      )}

      {/* AI Insights Panel */}
      <section>
        <AIInsightPanel />
      </section>
    </div>
  );
}
