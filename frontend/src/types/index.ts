/**
 * Types para a MoodAPI
 */

export type Sentiment = 'positive' | 'neutral' | 'negative';

export interface SentimentScore {
    label: Sentiment;
    score: number;
}

export interface AnalysisResult {
    sentiment: Sentiment;
    confidence: number;
    language: string;
    all_scores: SentimentScore[];
}

export interface AnalysisResponse extends AnalysisResult {
    text: string;
    cached: boolean;
    response_time_ms: number;
    timestamp: string;
    record_id?: string;
}

export interface HistoryItem {
    id: string;
    text: string;           // For compatibility with frontend usage
    text_preview?: string;  // From backend
    sentiment: Sentiment;
    confidence: number;
    language: string;
    created_at: string;
    all_scores?: SentimentScore[];
}

export interface HistoryFilters {
    sentiment?: Sentiment;
    language?: string;
    min_confidence?: number;
    max_confidence?: number;
    start_date?: string;
    end_date?: string;
    page?: number;
    limit?: number;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
}

export interface PaginationMeta {
    page: number;
    limit: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
}

export interface HistoryResponse {
    items: HistoryItem[];
    pagination: PaginationMeta;
    filters_applied?: Record<string, unknown>;
    query_time_ms?: number;
    cached?: boolean;
}

export interface AnalyticsResponse {
    sentiment_distribution: {
        positive: number;
        negative: number;
        neutral: number;
    };
    language_distribution: Array<{
        language: string;
        count: number;
        percentage: number;
    }>;
    daily_volume: Array<{
        date: string;
        count: number;
        avg_confidence: number;
    }>;
    period_days: number;
    total_analyses: number;
}

export interface StatsResponse {
    total_analyses: number;
    avg_confidence: number;
    high_confidence_percentage: number;
    sentiment_distribution: {
        positive: number;
        negative: number;
        neutral: number;
    };
    top_languages: Array<{
        language: string;
        count: number;
        percentage: number;
    }>;
    period: string;
    sentiment_trend: Array<{
        date: string;
        positive: number;
        negative: number;
        neutral: number;
    }>;
    timestamp: string;
}

export interface HealthResponse {
    status: 'healthy' | 'degraded' | 'unhealthy';
    services: {
        database: string;
        cache: string;
        model: string;
    };
    model_info?: {
        model_name: string;
        model_loaded: boolean;
        device: string;
    };
}

export interface MetricsResponse {
    requests_total: number;
    cache_hit_rate: number;
    avg_latency_ms: number;
    uptime_seconds: number;
}

// Auth types
export interface User {
    id: string;
    username: string;
    email: string;
    full_name?: string;
    is_active: boolean;
    is_admin: boolean;
    created_at: string;
    last_login?: string;
}

export interface LoginRequest {
    username: string;
    password: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    expires_in: number;
    user: User;
}
