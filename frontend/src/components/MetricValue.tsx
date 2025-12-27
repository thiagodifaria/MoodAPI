/**
 * MetricValue - Componente para exibir métricas com label, valor e trend
 */

interface MetricValueProps {
    label: string;
    value: string | number;
    unit?: string;
    trend?: number;
    subLabel?: string;
}

export function MetricValue({ label, value, unit, trend, subLabel }: MetricValueProps) {
    return (
        <div className="flex flex-col">
            <span className="text-slate-500 text-xs font-mono uppercase mb-1">{label}</span>
            <div className="flex items-baseline gap-2">
                <span className="text-2xl font-mono font-bold text-slate-100">{value}</span>
                {unit && <span className="text-slate-500 text-sm font-mono">{unit}</span>}
            </div>
            {trend !== undefined && (
                <span className={`text-xs font-mono mt-1 ${trend > 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                    {trend > 0 ? '▲' : '▼'} {Math.abs(trend)}%
                </span>
            )}
            {subLabel && <span className="text-slate-600 text-[10px] mt-1">{subLabel}</span>}
        </div>
    );
}

export default MetricValue;
