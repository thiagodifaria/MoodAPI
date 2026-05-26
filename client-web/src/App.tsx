import { useState } from 'react';
import { Sidebar } from './components';
import type { TabType } from './components';
import { 
  AnalyzePage, 
  BatchPage, 
  HistoryPage, 
  SearchPage, 
  HealthPage 
} from './pages';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('analyze');

  function renderContent() {
    switch (activeTab) {
      case 'analyze':
        return <AnalyzePage />;
      case 'batch':
        return <BatchPage />;
      case 'history':
        return <HistoryPage />;
      case 'search':
        return <SearchPage />;
      case 'health':
        return <HealthPage />;
      default:
        return <AnalyzePage />;
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans flex flex-col md:flex-row h-screen overflow-hidden">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
