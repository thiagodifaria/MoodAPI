/**
 * API Service - Cliente para MoodAPI
 */
import axios from 'axios';
import type {
    AnalysisResponse,
    HistoryResponse,
    HistoryFilters,
    AnalyticsResponse,
    StatsResponse,
    HealthResponse,
    TokenResponse,
    LoginRequest,
    User
} from '../types';

// Configuração base
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

class ApiService {
    private client;
    private token: string | null = null;

    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: 30000,
        });

        // Interceptor para adicionar token
        this.client.interceptors.request.use((config) => {
            if (this.token && config.headers) {
                config.headers.Authorization = `Bearer ${this.token}`;
            }
            return config;
        });

        // Carregar token do localStorage
        const savedToken = localStorage.getItem('moodapi_token');
        if (savedToken) {
            this.token = savedToken;
        }
    }

    // =====================
    // Auth endpoints
    // =====================

    async login(credentials: LoginRequest): Promise<TokenResponse> {
        const response = await this.client.post<TokenResponse>('/auth/login', credentials);
        this.token = response.data.access_token;
        localStorage.setItem('moodapi_token', this.token);
        return response.data;
    }

    async getCurrentUser(): Promise<User> {
        const response = await this.client.get<User>('/auth/me');
        return response.data;
    }

    logout(): void {
        this.token = null;
        localStorage.removeItem('moodapi_token');
    }

    isAuthenticated(): boolean {
        return !!this.token;
    }

    // =====================
    // Sentiment endpoints
    // =====================

    async analyze(text: string): Promise<AnalysisResponse> {
        const startTime = performance.now();
        const response = await this.client.post<AnalysisResponse>('/sentiment/analyze', { text });
        const endTime = performance.now();

        return {
            ...response.data,
            response_time_ms: response.data.response_time_ms || (endTime - startTime),
        };
    }

    async analyzeBatch(texts: string[]): Promise<{ results: AnalysisResponse[] }> {
        const response = await this.client.post<{ results: AnalysisResponse[] }>('/sentiment/analyze-batch', { texts });
        return response.data;
    }

    async getSentimentHealth(): Promise<HealthResponse> {
        const response = await this.client.get<HealthResponse>('/sentiment/health');
        return response.data;
    }

    // =====================
    // History endpoints
    // =====================

    async getHistory(filters?: HistoryFilters): Promise<HistoryResponse> {
        const params = new URLSearchParams();

        if (filters) {
            Object.entries(filters).forEach(([key, value]) => {
                if (value !== undefined && value !== null && value !== '') {
                    params.append(key, String(value));
                }
            });
        }

        const response = await this.client.get<HistoryResponse>('/history', { params });

        // Map text_preview to text for frontend compatibility
        response.data.items = response.data.items.map(item => ({
            ...item,
            text: item.text || (item as unknown as { text_preview?: string }).text_preview || ''
        }));

        return response.data;
    }

    async getAnalysisById(id: string): Promise<AnalysisResponse> {
        const response = await this.client.get<AnalysisResponse>(`/history/${id}`);
        return response.data;
    }

    async deleteAnalysis(id: string): Promise<void> {
        await this.client.delete(`/history/${id}`);
    }

    async getAnalytics(days: number = 30): Promise<AnalyticsResponse> {
        const response = await this.client.get<AnalyticsResponse>('/history/analytics', {
            params: { days }
        });
        return response.data;
    }

    async getStats(days: number = 30): Promise<StatsResponse> {
        // Convert days to period format expected by backend
        let period = '30d';
        if (days <= 7) period = '7d';
        else if (days <= 30) period = '30d';
        else if (days <= 90) period = '90d';
        else period = '1y';

        const response = await this.client.get<StatsResponse>('/history/stats', {
            params: { period }
        });
        return response.data;
    }

    // =====================
    // System endpoints
    // =====================

    async getHealth(): Promise<HealthResponse> {
        const response = await this.client.get<HealthResponse>('/health', {
            baseURL: (import.meta.env.VITE_API_URL as string)?.replace('/api/v1', '') || ''
        });
        return response.data;
    }

    async getMetrics(): Promise<Record<string, unknown>> {
        const response = await this.client.get<Record<string, unknown>>('/metrics', {
            baseURL: (import.meta.env.VITE_API_URL as string)?.replace('/api/v1', '') || ''
        });
        return response.data;
    }

    async getVersion(): Promise<{ version: string; name: string }> {
        const response = await this.client.get<{ version: string; name: string }>('/version', {
            baseURL: (import.meta.env.VITE_API_URL as string)?.replace('/api/v1', '') || ''
        });
        return response.data;
    }
}

// Singleton instance
export const api = new ApiService();
export default api;
