import React from 'react';
import { 
  MessageSquare, 
  Layers, 
  History, 
  Search, 
  Activity, 
  Server
} from 'lucide-react';

export type TabType = 'analyze' | 'batch' | 'history' | 'search' | 'health';

interface SidebarProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'analyze', name: 'Análise Unitária', icon: <MessageSquare className="w-4 h-4" /> },
    { id: 'batch', name: 'Análise em Lote', icon: <Layers className="w-4 h-4" /> },
    { id: 'history', name: 'Histórico (DB)', icon: <History className="w-4 h-4" /> },
    { id: 'search', name: 'Busca Semântica', icon: <Search className="w-4 h-4" /> },
    { id: 'health', name: 'Health Check', icon: <Activity className="w-4 h-4" /> },
  ];

  return (
    <aside className="w-full md:w-64 bg-white border-r border-slate-200 flex flex-col h-screen shrink-0">
      <div className="p-6 border-b border-slate-200">
        <div className="flex items-center gap-2 text-teal-700 font-bold text-lg">
          <Server className="w-6 h-6" />
          <span>MoodAPI</span>
        </div>
        <p className="text-xs text-slate-500 mt-1">Tester de API Local</p>
      </div>

      <nav className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-1">
          {tabs.map(tab => (
            <li key={tab.id}>
              <button
                onClick={() => setActiveTab(tab.id as TabType)}
                className={`w-full text-left px-6 py-2.5 text-sm flex items-center gap-3 transition-colors ${
                  activeTab === tab.id 
                    ? 'bg-teal-50 text-teal-700 border-r-2 border-teal-600 font-medium' 
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                <span className={`${activeTab === tab.id ? 'text-teal-600' : 'text-slate-400'}`}>
                  {tab.icon}
                </span>
                {tab.name}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;
