from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from app.core.models import Analysis, ApiStats
from app.core.schemas import (
    SentimentResult, 
    SentimentLabel, 
    DetailedAnalysisResponse,
    EmotionSet
)

class StorageService:
    """Serviço para armazenamento e recuperação de dados de análise."""
    
    async def store_analysis(
        self,
        db: Session,
        analysis_data: Dict[str, Any],
        analysis_type: str
    ):
        """
        Armazena os resultados da análise recebidos das rotas.
        Este método serve como ponte entre as rotas e o método save_analysis.
        
        Args:
            db: Sessão do banco de dados
            analysis_data: Dicionário com dados da análise
            analysis_type: Tipo de análise ('basic' ou 'detailed')
        """
        # Extrair dados do dicionário
        text = analysis_data.get('text', '')
        language = analysis_data.get('language', 'en')
        processing_time_ms = analysis_data.get('processing_time_ms', 0)
        
        # Extrair dados de sentimento
        sentiment_data = analysis_data.get('sentiment', {})
        sentiment_label = sentiment_data.get('label', 'neutral')
        sentiment_score = sentiment_data.get('score', 0.0)
        sentiment_confidence = sentiment_data.get('confidence', 0.0)
        
        # Extrair dados opcionais para análise detalhada
        emotions = analysis_data.get('emotions', None)
        entities = analysis_data.get('entities', None)
        keywords = analysis_data.get('keywords', None)
        
        # Converter o label para o enum apropriado, se necessário
        if isinstance(sentiment_label, str):
            try:
                sentiment_label = SentimentLabel(sentiment_label)
            except ValueError:
                sentiment_label = SentimentLabel.NEUTRAL
        
        # Chamar o método save_analysis para persistir os dados
        await self.save_analysis(
            db=db,
            text=text,
            language=language,
            sentiment_label=sentiment_label,
            sentiment_score=sentiment_score,
            sentiment_confidence=sentiment_confidence,
            emotions=emotions,
            entities=entities,
            keywords=keywords,
            processing_time_ms=processing_time_ms
        )
    
    @staticmethod
    async def save_analysis(
        db: Session,
        text: str,
        language: str,
        sentiment_label: SentimentLabel,
        sentiment_score: float,
        sentiment_confidence: float,
        emotions: Optional[Dict[str, float]] = None,
        entities: Optional[List[Dict[str, Any]]] = None,
        keywords: Optional[List[str]] = None,
        processing_time_ms: int = 0,
    ) -> Analysis:
        """
        Salva uma análise de sentimento no banco de dados.
        
        Args:
            db: Sessão do banco de dados
            text: Texto analisado
            language: Idioma do texto
            sentiment_label: Classificação do sentimento
            sentiment_score: Pontuação do sentimento
            sentiment_confidence: Confiança da análise
            emotions: Dicionário de emoções detectadas
            entities: Lista de entidades detectadas
            keywords: Lista de palavras-chave
            processing_time_ms: Tempo de processamento em milissegundos
            
        Returns:
            Objeto Analysis salvo
        """
        # Criar objeto Analysis - CORRIGIDO: usando 'confidence' em vez de 'sentiment_confidence'
        analysis = Analysis(
            text=text,
            timestamp=datetime.utcnow(),
            language=language,
            sentiment_label=sentiment_label.value,
            sentiment_score=sentiment_score,
            confidence=sentiment_confidence,  # Nome correto do campo no modelo
            processing_time_ms=processing_time_ms,
            full_analysis={
                "emotions": emotions,
                "entities": entities,
                "keywords": keywords
            } if emotions or entities or keywords else None
        )
        
        # Adicionar à sessão e comitar
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        # Atualizar estatísticas
        await StorageService.update_api_stats(db, processing_time_ms, False)
        
        return analysis
    
    @staticmethod
    async def update_api_stats(db: Session, response_time_ms: int, is_error: bool = False) -> None:
        """
        Atualiza estatísticas da API.
    
        Args:
            db: Sessão do banco de dados
            response_time_ms: Tempo de resposta em milissegundos
            is_error: Se a requisição resultou em erro
        """
        # Obter estatísticas atuais
        stats = db.query(ApiStats).first()
    
        if not stats:
            # Criar estatísticas iniciais se não existirem
            stats = ApiStats(
                requests_count=1,
                avg_response_time_ms=float(response_time_ms),
                error_count=1 if is_error else 0,
                date=datetime.utcnow()  # CORRIGIDO: Removido last_request
            )
            db.add(stats)
        else:
            # Atualizar estatísticas existentes
            total_time = stats.avg_response_time_ms * stats.requests_count
            stats.requests_count += 1
            stats.avg_response_time_ms = (total_time + response_time_ms) / stats.requests_count
            if is_error:
                stats.error_count += 1
            # CORRIGIDO: Não atualiza o campo last_request pois ele não existe no modelo
     
        db.commit()
    
    @staticmethod
    async def get_analysis_by_id(db: Session, analysis_id: int) -> Optional[Analysis]:
        """
        Recupera uma análise pelo ID.
        
        Args:
            db: Sessão do banco de dados
            analysis_id: ID da análise
            
        Returns:
            Objeto Analysis ou None se não encontrado
        """
        return db.query(Analysis).filter(Analysis.id == analysis_id).first()
    
    @staticmethod
    async def get_analysis_history(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        language: Optional[str] = None,
        sentiment: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[List[Analysis], int]:
        """
        Recupera histórico de análises com filtros e paginação.
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros para pular (para paginação)
            limit: Número máximo de registros a retornar
            language: Filtrar por idioma
            sentiment: Filtrar por sentimento
            start_date: Data de início para filtro
            end_date: Data de fim para filtro
            
        Returns:
            Tupla com lista de análises e contagem total
        """
        # Construir consulta base
        query = db.query(Analysis)
        
        # Aplicar filtros
        if language:
            query = query.filter(Analysis.language == language)
        if sentiment:
            query = query.filter(Analysis.sentiment_label == sentiment)
        if start_date:
            query = query.filter(Analysis.timestamp >= start_date)
        if end_date:
            query = query.filter(Analysis.timestamp <= end_date)
        
        # Obter contagem total
        total = query.count()
        
        # Aplicar paginação e ordenação
        results = query.order_by(desc(Analysis.timestamp)).offset(skip).limit(limit).all()
        
        return results, total
    
    @staticmethod
    async def get_stats(db: Session) -> ApiStats:
        """
        Recupera estatísticas da API.
    
        Args:
            db: Sessão do banco de dados
        
        Returns:
            Objeto ApiStats
        """
        stats = db.query(ApiStats).first()
        if not stats:
            # Criar estatísticas iniciais se não existirem
            stats = ApiStats(
                requests_count=0,
                avg_response_time_ms=0.0,  # Corrigido para usar o nome correto do campo
                error_count=0,
                date=datetime.utcnow()  # Removido o campo last_request
            )
            db.add(stats)
            db.commit()
            db.refresh(stats)
    
        return stats
    
    @staticmethod
    async def get_language_distribution(db: Session) -> Dict[str, int]:
        """
        Recupera distribuição de idiomas das análises.
        
        Args:
            db: Sessão do banco de dados
            
        Returns:
            Dicionário com contagem por idioma
        """
        result = db.query(
            Analysis.language, 
            func.count(Analysis.id).label('count')
        ).group_by(Analysis.language).all()
        
        return {r.language: r.count for r in result}
    
    @staticmethod
    async def get_sentiment_distribution(db: Session) -> Dict[str, int]:
        """
        Recupera distribuição de sentimentos das análises.
        
        Args:
            db: Sessão do banco de dados
            
        Returns:
            Dicionário com contagem por sentimento
        """
        result = db.query(
            Analysis.sentiment_label, 
            func.count(Analysis.id).label('count')
        ).group_by(Analysis.sentiment_label).all()
        
        return {r.sentiment_label: r.count for r in result}
    
    @staticmethod
    async def delete_analysis(db: Session, analysis_id: int) -> bool:
        """
        Exclui uma análise pelo ID.
        
        Args:
            db: Sessão do banco de dados
            analysis_id: ID da análise
            
        Returns:
            True se excluído com sucesso, False caso contrário
        """
        analysis = await StorageService.get_analysis_by_id(db, analysis_id)
        if not analysis:
            return False
        
        db.delete(analysis)
        db.commit()
        return True