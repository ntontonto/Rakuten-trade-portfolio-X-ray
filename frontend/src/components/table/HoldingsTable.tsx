import { useState } from 'react';
import type { Holding } from '../../types';
import { usePortfolioStore } from '../../stores/portfolioStore';
import { portfolioAPI } from '../../services/api';

interface HoldingsTableProps {
  holdings: Holding[];
}

export default function HoldingsTable({ holdings }: HoldingsTableProps) {
  const { currentPortfolio, setHoldings } = usePortfolioStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [editingSymbol, setEditingSymbol] = useState<string | null>(null);
  const [editPrice, setEditPrice] = useState('');

  const formatNumber = (value?: number, decimals = 2) => {
    if (value === undefined || value === null) return '-';
    return value.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const formatCurrency = (value?: number) => {
    if (value === undefined || value === null) return '-';
    return `¥${Math.floor(value).toLocaleString()}`;
  };

  const formatPercent = (value?: number) => {
    if (value === undefined || value === null) return '-';
    return `${(value * 100).toFixed(1)}%`;
  };

  const handlePriceEdit = (holding: Holding) => {
    setEditingSymbol(holding.symbol);
    setEditPrice(holding.current_price?.toString() || '');
  };

  const handlePriceSave = async (holding: Holding) => {
    if (!currentPortfolio) return;

    try {
      const newPrice = parseFloat(editPrice);
      if (isNaN(newPrice) || newPrice <= 0) {
        alert('Invalid price');
        return;
      }

      // Update via API
      await portfolioAPI.updateHoldingPrice(
        currentPortfolio.id,
        holding.symbol,
        newPrice
      );

      // Refresh holdings
      const updatedHoldings = await portfolioAPI.getHoldings(currentPortfolio.id);
      setHoldings(updatedHoldings);

      setEditingSymbol(null);
    } catch (error) {
      console.error('Failed to update price:', error);
      alert('Failed to update price');
    }
  };

  const filteredHoldings = holdings.filter(
    (h) =>
      h.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      h.symbol.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedHoldings = [...filteredHoldings].sort(
    (a, b) => (b.current_value || 0) - (a.current_value || 0)
  );

  return (
    <div>
      {/* Search */}
      <div className="p-4 border-b border-slate-200 bg-slate-50">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="銘柄名で検索..."
          className="px-3 py-1.5 text-sm border border-slate-300 rounded-md focus:outline-none focus:border-blue-500 w-64"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th>銘柄名 / ティッカー</th>
              <th>資産クラス</th>
              <th>戦略</th>
              <th className="text-right">保有数量</th>
              <th className="text-right">平均取得単価</th>
              <th className="text-right bg-blue-50 border-l border-blue-100">
                現在単価 (編集可)
              </th>
              <th className="text-right">評価額</th>
              <th className="text-right">含み損益</th>
              <th className="text-right">保有期間</th>
              <th className="text-right">推定XIRR</th>
            </tr>
          </thead>
          <tbody>
            {sortedHoldings.map((holding) => (
              <tr key={holding.id} className="hover:bg-slate-50 transition-colors">
                {/* Name */}
                <td>
                  <div className="font-bold text-slate-700 flex items-center gap-2">
                    {holding.name}
                    {holding.is_price_auto_updated && (
                      <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded border border-green-200">
                        自動
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-400">{holding.symbol}</div>
                </td>

                {/* Asset Class */}
                <td>
                  <span className="px-2 py-0.5 text-xs rounded bg-slate-100 text-slate-600 font-medium">
                    {holding.asset_class || '-'}
                  </span>
                </td>

                {/* Strategy */}
                <td>
                  <span
                    className={`px-2 py-0.5 text-xs rounded font-medium ${
                      holding.strategy === 'Core'
                        ? 'bg-indigo-100 text-indigo-700'
                        : 'bg-rose-100 text-rose-700'
                    }`}
                  >
                    {holding.strategy || '-'}
                  </span>
                </td>

                {/* Quantity */}
                <td className="text-right text-sm">
                  {formatNumber(holding.quantity, 4)}
                </td>

                {/* Average Cost */}
                <td className="text-right text-sm">
                  {formatCurrency(holding.average_cost)}
                </td>

                {/* Current Price (Editable) */}
                <td className="text-right bg-blue-50/30 border-l border-blue-100">
                  {editingSymbol === holding.symbol ? (
                    <input
                      type="number"
                      value={editPrice}
                      onChange={(e) => setEditPrice(e.target.value)}
                      onBlur={() => handlePriceSave(holding)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handlePriceSave(holding);
                        if (e.key === 'Escape') setEditingSymbol(null);
                      }}
                      className="input-price"
                      autoFocus
                    />
                  ) : (
                    <button
                      onClick={() => handlePriceEdit(holding)}
                      className={`input-price text-right w-full ${
                        holding.is_price_auto_updated ? 'auto-updated' : ''
                      }`}
                      title={
                        holding.is_price_auto_updated
                          ? '資産残高ファイルから自動取得済み'
                          : '手動入力が必要です'
                      }
                    >
                      {holding.current_price || '-'}
                    </button>
                  )}
                </td>

                {/* Current Value */}
                <td className="text-right font-bold text-slate-700">
                  {formatCurrency(holding.current_value)}
                </td>

                {/* Unrealized P&L */}
                <td
                  className={`text-right font-bold ${
                    (holding.unrealized_pl || 0) >= 0
                      ? 'text-emerald-600'
                      : 'text-red-500'
                  }`}
                >
                  {formatCurrency(holding.unrealized_pl)}
                </td>

                {/* Holding Days */}
                <td className="text-right text-sm text-slate-500">
                  {holding.holding_days ? `${holding.holding_days}日` : '-'}
                </td>

                {/* XIRR */}
                <td
                  className={`text-right font-bold ${
                    (holding.xirr || 0) >= 0 ? 'text-blue-600' : 'text-red-500'
                  }`}
                >
                  {formatPercent(holding.xirr)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {sortedHoldings.length === 0 && (
        <div className="p-8 text-center text-slate-500">
          {searchTerm ? '検索結果がありません' : '保有銘柄がありません'}
        </div>
      )}
    </div>
  );
}
