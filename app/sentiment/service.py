import hashlib
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.cache import CacheService
from app.core.exceptions import (
    DatabaseError,
    InvalidTextError,
    MLError,
    raise_for_text_validation,
)
from app.sentiment.analyzer import get_sentiment_analyzer
from app.sentiment.models import SentimentAnalysis

logger = logging.getLogger(__name__)
settings = get_settings()


class SentimentService:
    """Serviço de análise de sentimentos com integração ML+Cache+Database."""
    
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        self.analyzer = get_sentiment_analyzer()
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "analyses_performed": 0,
            "errors": 0,
        }
        logger.info("SentimentService inicializado")
    
    def _generate_cache_key(self, text: str) -> str:
        """Gera chave de cache determinística para o texto."""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"sentiment:analysis:{text_hash}"
    
    def _should_cache_result(self, result: Dict[str, Any]) -> bool:
        """Determina se resultado deve ser cacheado."""
        return (
            result.get("confidence", 0.0) >= settings.ml.confidence_threshold
            and not result.get("error")
            and len(result.get("sentiment", "")) > 0
        )
    
    async def analyze_text(
        self, 
        text: str, 
        db: Session, 
        use_cache: bool = True,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Analisa sentimento de um texto com fluxo: cache → ML → save → cache.
        
        Args:
            text: Texto para análise
            db: Sessão do banco de dados
            use_cache: Se deve usar cache (padrão: True)
            save_to_db: Se deve salvar no banco (padrão: True)
            
        Returns:
            Dict com resultado da análise
        """
        start_time = time.time()
        
        try:
            # Validar entrada
            raise_for_text_validation(
                text, 
                min_length=settings.ml.min_text_length,
                max_length=settings.ml.max_text_length
            )
            
            text_normalized = text.strip()
            cache_key = self._generate_cache_key(text_normalized)
            
            # 1. Verificar cache
            cached_result = None
            if use_cache:
                try:
                    cached_result = await self.cache_service.get(cache_key)
                    if cached_result:
                        self._stats["cache_hits"] += 1
                        logger.debug(f"Cache hit para análise de sentimentos")
                        
                        # Adicionar métricas de performance
                        cached_result["cached"] = True
                        cached_result["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
                        
                        return cached_result
                except Exception as e:
                    logger.warning(f"Erro ao buscar no cache: {e}")
            
            self._stats["cache_misses"] += 1
            
            # 2. Executar análise de ML
            logger.debug("Executando análise de ML")
            ml_result = self.analyzer.analyze(text_normalized)
            
            # 3. Preparar resultado para persistência
            analysis_result = {
                "text": text_normalized,
                "sentiment": ml_result["sentiment"],
                "confidence": ml_result["confidence"],
                "language": ml_result["language"],
                "all_scores": ml_result.get("all_scores", []),
                "cached": False,
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 4. Salvar no banco de dados
            if save_to_db:
                try:
                    db_record = SentimentAnalysis(
                        text=text_normalized,
                        sentiment=ml_result["sentiment"],
                        confidence=ml_result["confidence"],
                        language=ml_result["language"],
                        all_scores=ml_result.get("all_scores", [])
                    )
                    
                    db.add(db_record)
                    db.commit()
                    
                    analysis_result["record_id"] = str(db_record.id)
                    logger.debug(f"Análise salva no banco: {db_record.id}")
                    
                except Exception as e:
                    logger.error(f"Erro ao salvar no banco: {e}")
                    db.rollback()
                    raise DatabaseError(
                        message=f"Falha ao persistir análise: {str(e)}",
                        details={"text_length": len(text_normalized)}
                    ) from e
            
            # 5. Atualizar cache
            if use_cache and self._should_cache_result(ml_result):
                try:
                    # Criar versão para cache (sem dados sensíveis)
                    cache_data = analysis_result.copy()
                    cache_data.pop("text", None)  # Não cachear texto original por privacidade
                    
                    await self.cache_service.set(
                        cache_key, 
                        cache_data,
                        ttl=settings.cache.default_ttl
                    )
                    logger.debug("Resultado cacheado")
                except Exception as e:
                    logger.warning(f"Erro ao cachear resultado: {e}")
            
            self._stats["analyses_performed"] += 1
            logger.info(f"Análise concluída: {ml_result['sentiment']} ({ml_result['confidence']:.3f})")
            
            return analysis_result
            
        except (InvalidTextError, MLError, DatabaseError):
            self._stats["errors"] += 1
            raise
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Erro inesperado no serviço de sentimentos: {e}")
            raise MLError(
                message=f"Falha no serviço de análise: {str(e)}",
                details={"text_length": len(text) if text else 0}
            ) from e
    
    async def analyze_batch(
        self, 
        texts: List[str], 
        db: Session,
        use_cache: bool = True,
        save_to_db: bool = True,
        max_batch_size: int = None
    ) -> List[Dict[str, Any]]:
        """
        Analisa múltiplos textos em lote de forma otimizada.
        
        Args:
            texts: Lista de textos para análise
            db: Sessão do banco de dados
            use_cache: Se deve usar cache
            save_to_db: Se deve salvar no banco
            max_batch_size: Tamanho máximo do lote
            
        Returns:
            Lista de resultados de análise
        """
        if not texts:
            return []
        
        batch_size = min(
            len(texts), 
            max_batch_size or settings.ml.batch_size
        )
        
        logger.info(f"Processando lote de {len(texts)} textos (batch_size: {batch_size})")
        
        results = []
        
        # Processar em lotes menores se necessário
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = []
            
            # Verificar cache para todo o lote primeiro
            cache_hits = {}
            cache_misses = []
            
            if use_cache:
                for idx, text in enumerate(batch):
                    try:
                        raise_for_text_validation(text, settings.ml.min_text_length, settings.ml.max_text_length)
                        cache_key = self._generate_cache_key(text.strip())
                        cached_result = await self.cache_service.get(cache_key)
                        
                        if cached_result:
                            cache_hits[idx] = cached_result
                        else:
                            cache_misses.append((idx, text.strip()))
                    except Exception as e:
                        logger.warning(f"Erro na validação/cache do texto {i+idx}: {e}")
                        cache_misses.append((idx, text))
            else:
                cache_misses = [(idx, text.strip()) for idx, text in enumerate(batch)]
            
            # Processar textos não encontrados no cache
            if cache_misses:
                miss_texts = [text for _, text in cache_misses]
                
                try:
                    ml_results = self.analyzer.analyze_batch(miss_texts)
                    
                    # Salvar resultados no banco e cache
                    for (original_idx, text), ml_result in zip(cache_misses, ml_results):
                        try:
                            # Preparar resultado
                            analysis_result = {
                                "text": text,
                                "sentiment": ml_result["sentiment"],
                                "confidence": ml_result["confidence"],
                                "language": ml_result["language"],
                                "all_scores": ml_result.get("all_scores", []),
                                "cached": False,
                                "batch_index": original_idx,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            
                            # Salvar no banco
                            if save_to_db and not ml_result.get("error"):
                                db_record = SentimentAnalysis(
                                    text=text,
                                    sentiment=ml_result["sentiment"],
                                    confidence=ml_result["confidence"],
                                    language=ml_result["language"],
                                    all_scores=ml_result.get("all_scores", [])
                                )
                                db.add(db_record)
                                analysis_result["record_id"] = str(db_record.id)
                            
                            # Cachear se adequado
                            if use_cache and self._should_cache_result(ml_result):
                                cache_key = self._generate_cache_key(text)
                                cache_data = analysis_result.copy()
                                cache_data.pop("text", None)
                                
                                await self.cache_service.set(cache_key, cache_data)
                            
                            cache_hits[original_idx] = analysis_result
                            
                        except Exception as e:
                            logger.error(f"Erro ao processar resultado do lote {original_idx}: {e}")
                            cache_hits[original_idx] = {
                                "sentiment": "neutral",
                                "confidence": 0.0,
                                "language": "en",
                                "error": str(e),
                                "batch_index": original_idx
                            }
                    
                    # Commit das operações de banco em lote
                    if save_to_db:
                        try:
                            db.commit()
                        except Exception as e:
                            logger.error(f"Erro ao committar lote: {e}")
                            db.rollback()
                
                except Exception as e:
                    logger.error(f"Erro ao processar lote de ML: {e}")
                    # Preencher com resultados de erro
                    for original_idx, text in cache_misses:
                        cache_hits[original_idx] = {
                            "sentiment": "neutral",
                            "confidence": 0.0,
                            "language": "en",
                            "error": str(e),
                            "batch_index": original_idx
                        }
            
            # Montar resultados ordenados
            for idx in range(len(batch)):
                result = cache_hits.get(idx, {
                    "sentiment": "neutral",
                    "confidence": 0.0,
                    "language": "en",
                    "error": "Resultado não encontrado",
                    "batch_index": idx
                })
                
                if result.get("cached"):
                    self._stats["cache_hits"] += 1
                else:
                    self._stats["cache_misses"] += 1
                    self._stats["analyses_performed"] += 1
                
                batch_results.append(result)
            
            results.extend(batch_results)
        
        logger.info(f"Lote processado: {len(results)} resultados")
        return results
    
    async def get_analysis_history(
        self, 
        db: Session,
        limit: int = 100,
        offset: int = 0,
        sentiment_filter: Optional[str] = None,
        language_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recupera histórico de análises com filtros.
        
        Args:
            db: Sessão do banco
            limit: Limite de resultados
            offset: Offset para paginação
            sentiment_filter: Filtro por sentimento
            language_filter: Filtro por idioma
            
        Returns:
            Dict com resultados e metadados
        """
        try:
            query = db.query(SentimentAnalysis)
            
            # Aplicar filtros
            if sentiment_filter:
                query = query.filter(SentimentAnalysis.sentiment == sentiment_filter)
            
            if language_filter:
                query = query.filter(SentimentAnalysis.language == language_filter)
            
            # Ordenar por timestamp decrescente
            query = query.order_by(SentimentAnalysis.created_at.desc())
            
            # Contar total
            total_count = query.count()
            
            # Aplicar paginação
            records = query.offset(offset).limit(limit).all()
            
            # Converter para dict
            results = [
                {
                    "id": str(record.id),
                    "sentiment": record.sentiment,
                    "confidence": record.confidence,
                    "language": record.language,
                    "text_preview": record.text[:100] + "..." if len(record.text) > 100 else record.text,
                    "created_at": record.created_at.isoformat(),
                    "all_scores": record.all_scores
                }
                for record in records
            ]
            
            return {
                "results": results,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar histórico: {e}")
            raise DatabaseError(
                message=f"Falha ao recuperar histórico: {str(e)}",
                details={"limit": limit, "offset": offset}
            ) from e
    
    async def get_statistics(self, db: Session) -> Dict[str, Any]:
        """
        Recupera estatísticas do serviço e banco de dados.
        
        Returns:
            Dict com estatísticas completas
        """
        try:
            # Stats do serviço em memória
            service_stats = self._stats.copy()
            
            # Stats do cache
            cache_stats = await self.cache_service.get_stats()
            
            # Stats do banco de dados
            total_analyses = db.query(SentimentAnalysis).count()
            
            sentiment_distribution = db.query(
                SentimentAnalysis.sentiment,
                db.func.count(SentimentAnalysis.id).label('count')
            ).group_by(SentimentAnalysis.sentiment).all()
            
            language_distribution = db.query(
                SentimentAnalysis.language,
                db.func.count(SentimentAnalysis.id).label('count')
            ).group_by(SentimentAnalysis.language).all()
            
            # Stats do modelo
            model_info = self.analyzer.get_model_info()
            
            return {
                "service": service_stats,
                "cache": cache_stats,
                "database": {
                    "total_analyses": total_analyses,
                    "sentiment_distribution": [
                        {"sentiment": s, "count": c} for s, c in sentiment_distribution
                    ],
                    "language_distribution": [
                        {"language": l, "count": c} for l, c in language_distribution
                    ]
                },
                "model": model_info,
                "uptime_info": {
                    "cache_hit_rate": cache_stats.get("hit_rate", 0.0),
                    "service_hit_rate": (
                        service_stats["cache_hits"] / 
                        (service_stats["cache_hits"] + service_stats["cache_misses"])
                        if service_stats["cache_hits"] + service_stats["cache_misses"] > 0 
                        else 0.0
                    ),
                    "error_rate": (
                        service_stats["errors"] / 
                        (service_stats["analyses_performed"] + service_stats["errors"])
                        if service_stats["analyses_performed"] + service_stats["errors"] > 0
                        else 0.0
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            raise DatabaseError(
                message=f"Falha ao gerar estatísticas: {str(e)}"
            ) from e
    
    async def clear_cache(self) -> bool:
        """Limpa cache de análises."""
        try:
            result = await self.cache_service.clear_all()
            if result:
                logger.info("Cache de análises limpo")
            return result
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            return False