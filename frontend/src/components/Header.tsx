/**
 * Header - Barra superior com logo e status
 */
import { Activity } from 'lucide-react';

interface HeaderProps {
    isOnline: boolean;
}

export function Header({ isOnline }: HeaderProps) {
    return (
        <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md shrink-0 flex items-center justify-between px-6 z-50">
            <div className="flex items-center gap-3 transition-all duration-300">
                <div className="bg-amber-500 p-1.5 rounded-sm shadow-lg shadow-amber-500/20">
                    <Activity size={20} className="text-slate-900" />
                </div>
                <div>
                    <h1 className="text-lg font-bold text-slate-100 tracking-tight leading-none">
                        MoodAPI
                    </h1>
                    <p className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">
                        v1.0.0
                    </p>
                </div>
            </div>

            <div className="hidden md:flex items-center gap-6">
                <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${isOnline
                    ? 'bg-emerald-500/5 border-emerald-500/10'
                    : 'bg-rose-500/5 border-rose-500/10'
                    }`}>
                    <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
                        }`} />
                    <span className={`text-xs font-mono uppercase tracking-wide ${isOnline ? 'text-emerald-500' : 'text-rose-500'
                        }`}>
                        {isOnline ? 'Sistema Online' : 'Sistema Offline'}
                    </span>
                </div>
            </div>
        </header>
    );
}

export default Header;
