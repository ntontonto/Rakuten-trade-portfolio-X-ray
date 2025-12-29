import { Activity, Upload, FileDown } from 'lucide-react';

interface HeaderProps {
  onReload: () => void;
  portfolioName?: string;
}

export default function Header({ onReload, portfolioName }: HeaderProps) {
  return (
    <header className="bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-sm sticky top-0 z-40">
      <div className="max-w-[1400px] mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          {/* Logo & Name */}
          <div className="flex items-center gap-3">
            <Activity className="text-blue-600 w-6 h-6" />
            <span className="font-bold text-slate-700 text-lg tracking-tight">
              Portfolio X-Ray
            </span>
            {portfolioName && (
              <span className="text-sm text-slate-500">- {portfolioName}</span>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={onReload}
              className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md text-xs font-bold transition-colors"
            >
              <Upload className="w-3.5 h-3.5" />
              再読込
            </button>

            <button
              onClick={() => alert('PDF export coming soon!')}
              className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-md text-xs font-bold transition-colors"
            >
              <FileDown className="w-3.5 h-3.5" />
              PDF
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
