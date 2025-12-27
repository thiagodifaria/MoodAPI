/**
 * Sidebar - Menu lateral colapsável
 */
import { BarChart3, Terminal, Settings, ChevronLeft, ChevronRight, Info, Github, MessageSquareText } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export type TabType = 'dashboard' | 'analysis' | 'logs' | 'settings' | 'about';

interface SidebarItemProps {
    icon: LucideIcon;
    label: string;
    active: boolean;
    onClick: () => void;
    collapsed: boolean;
}

function SidebarItem({ icon: Icon, label, active, onClick, collapsed }: SidebarItemProps) {
    return (
        <button
            onClick={onClick}
            className={`
        flex items-center gap-3 p-3 rounded-xl transition-all w-full
        ${active
                    ? 'bg-amber-500/10 text-amber-500 ring-1 ring-amber-500/50 shadow-[0_0_15px_rgba(245,158,11,0.1)]'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800'
                }
      `}
            title={collapsed ? label : ''}
        >
            <Icon size={22} className="shrink-0" />
            {!collapsed && (
                <span className="font-mono text-sm tracking-wide whitespace-nowrap overflow-hidden transition-all duration-300">
                    {label}
                </span>
            )}
        </button>
    );
}

interface SidebarProps {
    activeTab: TabType;
    setActiveTab: (tab: TabType) => void;
    collapsed: boolean;
    setCollapsed: (collapsed: boolean) => void;
}

export function Sidebar({ activeTab, setActiveTab, collapsed, setCollapsed }: SidebarProps) {
    const menuItems: { icon: LucideIcon; label: string; tab: TabType }[] = [
        { icon: BarChart3, label: 'Dashboard', tab: 'dashboard' },
        { icon: MessageSquareText, label: 'Análises', tab: 'analysis' },
        { icon: Terminal, label: 'Logs & Histórico', tab: 'logs' },
        { icon: Settings, label: 'Configurações', tab: 'settings' },
        { icon: Info, label: 'Sobre', tab: 'about' },
    ];

    return (
        <aside
            className={`
        bg-slate-900 border-r border-slate-800 flex flex-col py-4 gap-2 z-40 transition-all duration-300 ease-in-out relative
        ${collapsed ? 'w-20 items-center' : 'w-74 px-4'}
      `}
        >
            {/* Toggle Button */}
            <button
                onClick={() => setCollapsed(!collapsed)}
                className="absolute -right-3 top-6 bg-slate-800 border border-slate-600 text-slate-400 p-1 rounded-full hover:bg-slate-700 hover:text-white transition-colors z-50 shadow-md"
            >
                {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
            </button>

            <div className="flex-1 space-y-2 mt-2">
                {menuItems.map((item) => (
                    <SidebarItem
                        key={item.tab}
                        icon={item.icon}
                        label={item.label}
                        active={activeTab === item.tab}
                        onClick={() => setActiveTab(item.tab)}
                        collapsed={collapsed}
                    />
                ))}
            </div>

            {/* Footer */}
            <div className={`border-t border-slate-800 pt-4 mt-2 ${collapsed ? 'px-2' : ''}`}>
                {!collapsed ? (
                    <div className="text-center space-y-2">
                        <p className="text-[10px] text-slate-600 font-mono">
                            Criado por
                        </p>
                        <a
                            href="https://github.com/thiagodifaria"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center justify-center gap-2 text-slate-400 hover:text-amber-500 transition-colors"
                        >
                            <Github size={14} />
                            <span className="text-xs font-mono">Thiago Di Faria</span>
                        </a>
                    </div>
                ) : (
                    <a
                        href="https://github.com/thiagodifaria"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-center text-slate-400 hover:text-amber-500 transition-colors p-2"
                        title="Thiago Di Faria"
                    >
                        <Github size={18} />
                    </a>
                )}
            </div>
        </aside>
    );
}

export default Sidebar;
