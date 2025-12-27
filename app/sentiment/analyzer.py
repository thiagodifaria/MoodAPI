import logging
import threading
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

import torch
from langdetect import DetectorFactory, LangDetectException, detect
from transformers import pipeline

from app.config import get_settings
from app.core.exceptions import (
    InvalidTextError,
    MLError,
    ModelInferenceError,
    ModelLoadError,
    ModelNotAvailableError,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Configurar langdetect para resultados consistentes
DetectorFactory.seed = 0


class SentimentAnalyzerMeta(type):
    """Metaclass thread-safe para implementar singleton pattern."""
    
    _instances: Dict[type, Any] = {}
    _lock: threading.Lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                # Double-check locking pattern
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
                    logger.info(f"Instância singleton criada: {cls.__name__}")
        return cls._instances[cls]


class SentimentAnalyzer(metaclass=SentimentAnalyzerMeta):
    """Engine de Machine Learning para análise de sentimentos multilíngue.
    
    Implementa lazy loading: modelo só é carregado na primeira análise.
    """
    
    def __init__(self):
        self._pipeline = None
        self._device = None
        self._model_loaded = False
        self._loading = False  # Flag para evitar carregamento duplo
        self._lock = threading.Lock()
        # LAZY LOADING: NÃO carrega modelo no init
        logger.info("SentimentAnalyzer inicializado (modelo será carregado sob demanda)")
    
    def _ensure_model_loaded(self) -> None:
        """Garante que o modelo está carregado (lazy loading thread-safe)."""
        if self._model_loaded:
            return
        
        with self._lock:
            # Double-check locking
            if not self._model_loaded and not self._loading:
                self._loading = True
                try:
                    self._load_model()
                finally:
                    self._loading = False
    
    def _load_model(self) -> None:
        """Carrega modelo transformer uma única vez."""
        if self._model_loaded:
            return
            
        try:
            logger.info(f"Carregando modelo: {settings.ml.model_name}")
            
            # Detectar dispositivo
            self._device = self._get_device()
            logger.info(f"Dispositivo selecionado: {self._device}")
            
            # FIXED: Configuração atualizada para Transformers 4.35+
            pipeline_kwargs = {
                "task": "sentiment-analysis",
                "model": settings.ml.model_name,
                "device": self._device,
                "truncation": True,
                "padding": True,
                "max_length": settings.ml.max_text_length,
                "model_kwargs": {
                    "cache_dir": settings.ml.model_cache_dir,
                    "torch_dtype": torch.float16 if self._device >= 0 else torch.float32,
                }
            }
            
            # FIXED: Usar top_k em vez de return_all_scores (depreciado)
            try:
                # Tentar nova sintaxe primeiro (Transformers 4.35+)
                pipeline_kwargs["top_k"] = None  # Retorna todos os scores
                self._pipeline = pipeline(**pipeline_kwargs)
                logger.info("Pipeline criado com parâmetro 'top_k' (Transformers 4.35+)")
                
            except (TypeError, ValueError) as e:
                # Fallback para sintaxe antiga se top_k não funcionar
                logger.warning(f"Parâmetro 'top_k' falhou ({e}), usando 'return_all_scores'")
                pipeline_kwargs.pop("top_k", None)
                pipeline_kwargs["return_all_scores"] = True
                self._pipeline = pipeline(**pipeline_kwargs)
                logger.info("Pipeline criado com parâmetro 'return_all_scores' (Transformers <4.35)")
            
            self._model_loaded = True
            logger.info("Modelo carregado com sucesso")
            
            # Teste rápido para verificar funcionamento
            self._test_model()
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            raise ModelLoadError(
                model_name=settings.ml.model_name,
                message="Falha ao carregar modelo transformer",
                details={"error": str(e), "device": str(self._device)}
            ) from e
    
    def _get_device(self) -> int:
        """Determina dispositivo otimizado para inferência."""
        device_config = settings.ml.device.lower()
        
        if device_config == "cpu":
            return -1
        elif device_config == "cuda" and torch.cuda.is_available():
            return 0
        elif device_config == "auto":
            return 0 if torch.cuda.is_available() else -1
        else:
            logger.warning(f"Configuração de dispositivo inválida: {device_config}, usando CPU")
            return -1
    
    def _test_model(self) -> None:
        """Testa modelo com texto simples para verificar funcionamento."""
        try:
            test_result = self._pipeline("test")
            if not test_result:
                raise ModelInferenceError("Teste do modelo retornou resultado vazio")
            
            # FIXED: Verificar ambos os formatos possíveis
            if isinstance(test_result, list) and len(test_result) > 0:
                # Verificar se é formato novo (lista de listas) ou antigo (lista de dicts)
                first_item = test_result[0]
                if isinstance(first_item, list):
                    logger.debug("Modelo retorna formato aninhado (Transformers 4.35+)")
                elif isinstance(first_item, dict):
                    logger.debug("Modelo retorna formato plano (Transformers <4.35)")
                else:
                    raise ModelInferenceError(f"Formato de resultado inesperado: {type(first_item)}")
            else:
                raise ModelInferenceError("Teste do modelo retornou resultado inválido")
            
            logger.debug("Teste do modelo concluído com sucesso")
            
        except Exception as e:
            raise ModelLoadError(
                model_name=settings.ml.model_name,
                message="Modelo carregado mas teste de inferência falhou",
                details={"test_error": str(e)}
            ) from e
    
    def _detect_language(self, text: str) -> str:
        """Detecta idioma do texto com fallback robusto."""
        try:
            # Usar apenas os primeiros 1000 caracteres para detecção
            detection_text = text[:1000].strip()
            
            if len(detection_text) < 3:
                logger.debug("Texto muito curto para detecção, usando fallback 'en'")
                return "en"
            
            detected_lang = detect(detection_text)
            logger.debug(f"Idioma detectado: {detected_lang}")
            return detected_lang
            
        except LangDetectException as e:
            logger.debug(f"Erro na detecção de idioma: {e}, usando fallback 'en'")
            return "en"
        except Exception as e:
            logger.warning(f"Erro inesperado na detecção de idioma: {e}, usando fallback 'en'")
            return "en"
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para análise."""
        if not text or not text.strip():
            raise InvalidTextError(
                reason="Texto vazio ou apenas espaços",
                text_sample=text
            )
        
        # Limpar e normalizar
        normalized = text.strip()
        
        # Verificar limites
        if len(normalized) < settings.ml.min_text_length:
            raise InvalidTextError(
                reason=f"Texto muito curto (mínimo: {settings.ml.min_text_length} caracteres)",
                text_sample=normalized,
                details={"text_length": len(normalized)}
            )
        
        if len(normalized) > settings.ml.max_text_length:
            logger.debug(f"Texto truncado de {len(normalized)} para {settings.ml.max_text_length} caracteres")
            normalized = normalized[:settings.ml.max_text_length]
        
        return normalized
    
    def _flatten_results(self, raw_results: Union[List[Dict], List[List[Dict]]]) -> List[Dict]:
        """
        FIXED: Normaliza resultados para formato plano, lidando com ambos os formatos.
        
        Args:
            raw_results: Resultado do pipeline (formato antigo ou novo)
            
        Returns:
            Lista plana de dicionários com scores
        """
        try:
            if not raw_results or not isinstance(raw_results, list):
                raise ModelInferenceError("Resultado do modelo inválido ou vazio")
            
            # Verificar formato do primeiro item
            first_item = raw_results[0]
            
            if isinstance(first_item, dict):
                # Formato antigo: lista plana de dicts
                logger.debug("Processando formato antigo (lista plana)")
                return raw_results
                
            elif isinstance(first_item, list):
                # Formato novo: lista aninhada - pegar o primeiro subarray
                logger.debug("Processando formato novo (lista aninhada)")
                if len(first_item) > 0 and isinstance(first_item[0], dict):
                    return first_item
                else:
                    raise ModelInferenceError("Formato aninhado inválido")
                    
            else:
                raise ModelInferenceError(f"Formato inesperado: {type(first_item)}")
                
        except Exception as e:
            logger.error(f"Erro ao normalizar formato: {e}")
            raise ModelInferenceError(
                message=f"Erro ao processar formato do modelo: {str(e)}",
                details={"raw_results_type": str(type(raw_results)), "raw_results_sample": str(raw_results)[:200]}
            ) from e
    
    def _normalize_sentiment_result(self, raw_results: Union[List[Dict], List[List[Dict]]]) -> Dict[str, Any]:
        """FIXED: Normaliza resultado do modelo para formato padrão com compatibilidade total."""
        try:
            # FIXED: Primeiro, normalizar o formato
            flattened_results = self._flatten_results(raw_results)
            
            # Mapear labels do modelo para formato padrão
            label_mapping = {
                "POSITIVE": "positive",
                "NEGATIVE": "negative", 
                "NEUTRAL": "neutral",
                "LABEL_0": "negative",  # cardiffnlp format
                "LABEL_1": "neutral",   # cardiffnlp format
                "LABEL_2": "positive",  # cardiffnlp format
            }
            
            # Processar scores
            normalized_scores = []
            for result in flattened_results:
                if not isinstance(result, dict):
                    logger.warning(f"Item inválido ignorado: {result}")
                    continue
                    
                label = result.get("label", "").upper()
                score = float(result.get("score", 0.0))
                
                normalized_label = label_mapping.get(label, "neutral")
                normalized_scores.append({
                    "label": normalized_label,
                    "score": score
                })
            
            if not normalized_scores:
                raise ModelInferenceError("Nenhum score válido encontrado")
            
            # Encontrar resultado com maior confiança
            best_result = max(normalized_scores, key=lambda x: x["score"])
            
            return {
                "sentiment": best_result["label"],
                "confidence": round(best_result["score"], 4),
                "all_scores": normalized_scores
            }
            
        except ModelInferenceError:
            raise
        except Exception as e:
            logger.error(f"Erro ao normalizar resultado: {e}")
            raise ModelInferenceError(
                message=f"Erro ao processar resultado do modelo: {str(e)}",
                details={"raw_results": str(raw_results)[:200]}
            ) from e
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analisa sentimento do texto.
        
        Args:
            text: Texto para análise
            
        Returns:
            Dict contendo: sentiment, confidence, language, all_scores
            
        Raises:
            ModelNotAvailableError: Se modelo não estiver carregado
            InvalidTextError: Se texto for inválido
            ModelInferenceError: Se análise falhar
        """
        # LAZY LOADING: Garante que modelo está carregado
        self._ensure_model_loaded()
        
        if not self._model_loaded or not self._pipeline:
            raise ModelNotAvailableError(
                model_name=settings.ml.model_name,
                details={"model_loaded": self._model_loaded}
            )
        
        try:
            # Normalizar texto
            normalized_text = self._normalize_text(text)
            
            # Detectar idioma
            language = self._detect_language(normalized_text)
            
            # Executar análise de sentimento
            with self._lock:
                raw_results = self._pipeline(normalized_text)
            
            # FIXED: Normalizar resultado com nova lógica
            sentiment_result = self._normalize_sentiment_result(raw_results)
            
            # Montar resultado final
            final_result = {
                "sentiment": sentiment_result["sentiment"],
                "confidence": sentiment_result["confidence"],
                "language": language,
                "all_scores": sentiment_result["all_scores"]
            }
            
            logger.debug(f"Análise concluída: {final_result['sentiment']} ({final_result['confidence']})")
            return final_result
            
        except (InvalidTextError, ModelInferenceError, ModelNotAvailableError):
            raise
        except Exception as e:
            logger.error(f"Erro inesperado na análise: {e}")
            raise ModelInferenceError(
                message=f"Falha na análise de sentimentos: {str(e)}",
                details={"text_length": len(text) if text else 0}
            ) from e
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analisa múltiplos textos em lote usando processamento batch nativo.
        
        OTIMIZADO: Usa o pipeline batch do Transformers para melhor performance.
        
        Args:
            texts: Lista de textos para análise
            
        Returns:
            Lista de resultados de análise
        """
        if not texts:
            return []
        
        # LAZY LOADING: Garante que modelo está carregado
        self._ensure_model_loaded()
        
        if not self._model_loaded or not self._pipeline:
            raise ModelNotAvailableError(
                model_name=settings.ml.model_name,
                details={"model_loaded": self._model_loaded}
            )
        
        results = []
        batch_size = settings.ml.batch_size
        
        logger.debug(f"Processando {len(texts)} textos com batch nativo (size={batch_size})")
        
        try:
            # Pré-processar todos os textos
            normalized_texts = []
            languages = []
            valid_indices = []
            
            for i, text in enumerate(texts):
                try:
                    normalized = self._normalize_text(text)
                    lang = self._detect_language(normalized)
                    normalized_texts.append(normalized)
                    languages.append(lang)
                    valid_indices.append(i)
                except InvalidTextError as e:
                    logger.warning(f"Texto {i} inválido: {e}")
                    # Placeholder para manter ordem
                    normalized_texts.append(None)
                    languages.append("en")
            
            # BATCH NATIVO: Processa todos os textos válidos de uma vez
            valid_texts = [t for t in normalized_texts if t is not None]
            
            if valid_texts:
                with self._lock:
                    # Pipeline batch nativo - MUITO mais eficiente
                    raw_batch_results = self._pipeline(
                        valid_texts,
                        batch_size=batch_size
                    )
                
                # Mapear resultados de volta
                valid_idx = 0
                for i, text in enumerate(normalized_texts):
                    if text is not None:
                        try:
                            raw_result = raw_batch_results[valid_idx]
                            sentiment_result = self._normalize_sentiment_result([raw_result] if isinstance(raw_result, dict) else raw_result)
                            results.append({
                                "sentiment": sentiment_result["sentiment"],
                                "confidence": sentiment_result["confidence"],
                                "language": languages[i],
                                "all_scores": sentiment_result["all_scores"]
                            })
                        except Exception as e:
                            logger.error(f"Erro ao processar resultado {i}: {e}")
                            results.append(self._create_error_result(str(e)))
                        valid_idx += 1
                    else:
                        results.append(self._create_error_result("Texto inválido"))
            else:
                # Todos os textos eram inválidos
                results = [self._create_error_result("Texto inválido") for _ in texts]
            
            logger.debug(f"Batch processing concluído: {len(results)} resultados")
            return results
            
        except Exception as e:
            logger.error(f"Erro no batch processing: {e}")
            # Fallback: processar um por um
            logger.warning("Fallback para processamento sequencial")
            return [self.analyze(text) if text else self._create_error_result("Texto vazio") for text in texts]
    
    def _create_error_result(self, error_msg: str) -> Dict[str, Any]:
        """Cria resultado de erro padronizado."""
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "language": "en",
            "all_scores": [],
            "error": error_msg
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o modelo carregado."""
        # Handle lazy loading - device may be None if model not loaded
        device = "not_loaded"
        if self._device is not None:
            device = "cuda" if self._device >= 0 else "cpu"
        
        return {
            "model_name": settings.ml.model_name,
            "model_loaded": self._model_loaded,
            "device": device,
            "max_text_length": settings.ml.max_text_length,
            "min_text_length": settings.ml.min_text_length,
            "batch_size": settings.ml.batch_size,
            "transformers_compatibility": "4.35+",
        }


@lru_cache()
def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Factory singleton para obter instância do analisador."""
    return SentimentAnalyzer()