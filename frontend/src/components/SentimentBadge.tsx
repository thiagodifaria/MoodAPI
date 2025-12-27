/**
 * SentimentBadge - Badge colorido para exibir sentimento
 */
import type { Sentiment } from '../types';

const MOOD_COLORS: Record<Sentiment, string> = {
    positive: '#10b981',
    neutral: '#f59e0b',
    negative: '#ef4444',
};

interface SentimentBadgeProps {
    sentiment: Sentiment;
    className?: string;
}

export function SentimentBadge({ sentiment, className = '' }: SentimentBadgeProps) {
    const color = MOOD_COLORS[sentiment];

    return (
        <span
            className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase w-20 text-center ${className}`}
            style={{
                backgroundColor: `${color}20`,
                color: color,
                border: `1px solid ${color}40`,
            }}
        >
            {sentiment}
        </span>
    );
}

export function getMoodColor(sentiment: Sentiment): string {
    return MOOD_COLORS[sentiment];
}

export default SentimentBadge;
