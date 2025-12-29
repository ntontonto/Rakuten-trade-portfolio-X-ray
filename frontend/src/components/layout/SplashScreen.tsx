import { useState, useRef } from 'react';
import { Upload, PieChart } from 'lucide-react';
import { usePortfolioStore } from '../../stores/portfolioStore';

interface SplashScreenProps {
  onFilesSelected: (files: FileList) => void;
}

export default function SplashScreen({ onFilesSelected }: SplashScreenProps) {
  const { isLoading, error } = usePortfolioStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFilesSelected(e.target.files);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFilesSelected(e.dataTransfer.files);
    }
  };

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-slate-50 to-slate-200 flex flex-col items-center justify-center p-10">
      <div className="text-center max-w-2xl w-full">
        {/* Logo */}
        <div className="mb-6 flex justify-center">
          <div className="bg-white p-6 rounded-3xl shadow-xl border border-blue-100">
            <PieChart className="w-20 h-20 text-blue-600" />
          </div>
        </div>

        {/* Title */}
        <h1 className="text-4xl font-extrabold text-slate-800 mb-3 tracking-tight">
          Portfolio X-Ray
        </h1>
        <p className="text-slate-500 mb-8 font-medium text-lg">
          XIRR（内部収益率）と資産配分を可視化する
          <br />
          高度な投資分析ダッシュボード
        </p>

        {/* Upload Area */}
        <div className="bg-white p-8 rounded-2xl shadow-lg border border-slate-200">
          <p className="text-sm text-slate-500 mb-4">
            楽天証券のCSVファイルを読み込んでください
            <br />
            <span className="text-xs text-slate-400">
              （取引履歴・資産残高ファイルをまとめて選択可）
            </span>
          </p>

          {/* Drag and Drop Zone */}
          <div
            className={`border-2 border-dashed rounded-xl p-8 transition-all ${
              dragActive
                ? 'border-blue-500 bg-blue-50'
                : 'border-slate-300 hover:border-blue-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
              disabled={isLoading}
            />

            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-lg font-bold py-4 px-8 rounded-xl transition-all shadow-lg hover:shadow-blue-500/30 active:scale-95"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-6 w-6 border-4 border-white border-t-transparent"></div>
                  <span>処理中...</span>
                </>
              ) : (
                <>
                  <Upload className="w-6 h-6" />
                  <span>ファイルを選択 (複数可)</span>
                </>
              )}
            </button>

            {!isLoading && (
              <p className="text-xs text-slate-400 mt-4">
                またはファイルをドラッグ＆ドロップ
              </p>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700 font-medium">{error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
