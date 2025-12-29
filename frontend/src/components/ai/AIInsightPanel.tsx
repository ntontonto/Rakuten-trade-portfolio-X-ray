import { useState } from 'react';
import { Sparkles, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { portfolioAPI } from '../../services/api';
import { usePortfolioStore } from '../../stores/portfolioStore';

export default function AIInsightPanel() {
  const { currentPortfolio } = usePortfolioStore();
  const [insights, setInsights] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateInsights = async () => {
    if (!currentPortfolio) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await portfolioAPI.generateInsights(currentPortfolio.id);
      setInsights(result.insights);
    } catch (err: any) {
      console.error('Failed to generate insights:', err);
      setError(err.response?.data?.detail || 'AI分析に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl border border-purple-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-purple-600" />
          <h3 className="text-lg font-bold text-slate-800">
            AI ポートフォリオ分析
          </h3>
        </div>
        <button
          onClick={generateInsights}
          disabled={isLoading}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              分析中...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              分析を実行
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {insights ? (
        <div className="bg-white rounded-lg p-5 prose prose-sm max-w-none">
          <ReactMarkdown>{insights}</ReactMarkdown>
        </div>
      ) : (
        <div className="text-center py-8 text-slate-400">
          <p className="text-sm">
            「分析を実行」ボタンをクリックして、AI によるポートフォリオ分析を取得
          </p>
        </div>
      )}
    </div>
  );
}
