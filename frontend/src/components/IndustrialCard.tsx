/**
 * IndustrialCard - Card component com estilo terminal/industrial
 */
import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

interface IndustrialCardProps {
    title: string;
    children: ReactNode;
    className?: string;
    icon?: LucideIcon;
    actions?: ReactNode;
}

export function IndustrialCard({
    title,
    children,
    className = '',
    icon: Icon,
    actions
}: IndustrialCardProps) {
    return (
        <div className={`bg-slate-900 border border-slate-700 shadow-lg relative overflow-hidden flex flex-col ${className}`}>
            {/* Corner decorations */}
            <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-amber-500/50" />
            <div className="absolute top-0 right-0 w-2 h-2 border-t-2 border-r-2 border-amber-500/50" />
            <div className="absolute bottom-0 left-0 w-2 h-2 border-b-2 border-l-2 border-amber-500/50" />
            <div className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-amber-500/50" />

            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm">
                <h3 className="text-xs font-mono font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2">
                    {Icon && <Icon size={14} className="text-amber-500" />}
                    {title}
                </h3>
                <div className="flex items-center gap-2">
                    {actions}
                    <div className="flex gap-1 ml-2">
                        <div className="w-1 h-1 rounded-full bg-slate-600" />
                        <div className="w-1 h-1 rounded-full bg-slate-600" />
                        <div className="w-1 h-1 rounded-full bg-slate-600" />
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="p-4 flex-1 relative z-10">
                {children}
            </div>

            {/* Grid pattern overlay */}
            <div className="absolute inset-0 grid-pattern pointer-events-none z-0" />
        </div>
    );
}

export default IndustrialCard;
