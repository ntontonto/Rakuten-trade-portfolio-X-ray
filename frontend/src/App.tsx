import { useState, useEffect } from 'react';
import { usePortfolioStore } from './stores/portfolioStore';
import { portfolioAPI } from './services/api';
import SplashScreen from './components/layout/SplashScreen';
import Header from './components/layout/Header';
import Dashboard from './components/layout/Dashboard';

function App() {
  const { currentPortfolio, summary, setCurrentPortfolio, setSummary, setHoldings, setMetrics, setLoading, setError } = usePortfolioStore();
  const [showSplash, setShowSplash] = useState(true);

  const handleFilesUploaded = async (files: FileList) => {
    try {
      setLoading(true);
      setError(null);

      const result = await portfolioAPI.uploadCSV(files);

      // Set portfolio data
      setCurrentPortfolio({
        id: result.portfolio_id,
        name: 'Main Portfolio',
        created_at: new Date().toISOString(),
      });
      setSummary(result.summary);

      // Fetch detailed data
      const [holdings, metrics] = await Promise.all([
        portfolioAPI.getHoldings(result.portfolio_id),
        portfolioAPI.getMetrics(result.portfolio_id),
      ]);

      setHoldings(holdings);
      setMetrics(metrics);

      // Hide splash screen
      setShowSplash(false);
    } catch (error: any) {
      setError(error.response?.data?.detail || error.message || 'Upload failed');
      console.error('Upload error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReload = () => {
    setShowSplash(true);
  };

  return (
    <div className="min-h-screen">
      {showSplash ? (
        <SplashScreen onFilesSelected={handleFilesUploaded} />
      ) : (
        <>
          <Header onReload={handleReload} portfolioName={currentPortfolio?.name} />
          <main className="app-container">
            <Dashboard />
          </main>
        </>
      )}
    </div>
  );
}

export default App;
