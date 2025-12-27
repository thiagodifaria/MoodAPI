/**
 * MoodAPI Dashboard - Main Application
 */
import { useState, useEffect } from 'react';
import { Header, Sidebar } from './components';
import type { TabType } from './components';
import { DashboardPage, AnalysisPage, LogsPage, SettingsPage, AboutPage } from './pages';
import { api } from './services/api';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isOnline, setIsOnline] = useState(true);

  // Check system health periodically
  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 60000); // Every 60s
    return () => clearInterval(interval);
  }, []);

  async function checkHealth() {
    try {
      const health = await api.getSentimentHealth();
      setIsOnline(health.status === 'healthy' || health.status === 'degraded');
    } catch (err) {
      setIsOnline(false);
    }
  }

  function renderContent() {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardPage />;
      case 'analysis':
        return <AnalysisPage />;
      case 'logs':
        return <LogsPage />;
      case 'settings':
        return <SettingsPage />;
      case 'about':
        return <AboutPage />;
      default:
        return <DashboardPage />;
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-300 font-sans flex flex-col h-screen overflow-hidden">
      <Header isOnline={isOnline} />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          collapsed={sidebarCollapsed}
          setCollapsed={setSidebarCollapsed}
        />

        <main className="flex-1 overflow-y-auto bg-slate-950 scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent p-4 md:p-8">
          <div className="max-w-7xl mx-auto">
            {renderContent()}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
