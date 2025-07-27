from typing import Dict, Any, Optional
from dataclasses import dataclass
import os
import tempfile
from datetime import datetime

from .vision_analyzer import VisionAnalyzer, VisionAnalysisResult
from .audio_analyzer import AudioAnalyzer, AudioAnalysisResult
from .content_analyzer import ContentAnalyzer, ContentAnalysisResult
from ..core.config import settings

@dataclass
class OverallAnalysisResult:
    # Individual analysis results
    vision_analysis: VisionAnalysisResult
    audio_analysis: AudioAnalysisResult
    content_analysis: ContentAnalysisResult
    
    # Overall scores
    body_language_score: float  # 25 points
    voice_score: float          # 25 points
    content_flow_score: float   # 25 points
    interaction_score: float    # 25 points
    total_score: float          # 100 points
    
    # Metadata
    video_duration: float
    analysis_timestamp: datetime
    recommendations: list

class AnalysisOrchestrator:
    def __init__(self):
        self.vision_analyzer = VisionAnalyzer()
        self.audio_analyzer = AudioAnalyzer()
        
        # Content analyzer (Gemini API gerektirir)
        if settings.GEMINI_API_KEY:
            self.content_analyzer = ContentAnalyzer(settings.GEMINI_API_KEY)
        else:
            self.content_analyzer = None
            print("Uyarı: GEMINI_API_KEY bulunamadı. İçerik analizi devre dışı.")
    
    async def analyze_video(self, video_path: str, subject_topic: Optional[str] = None) -> OverallAnalysisResult:
        """
        Video'yu tüm modüllerle analiz et ve birleşik sonuç döndür
        """
        print(f"Video analizi başlıyor: {video_path}")
        
        # Video süresini hesapla
        video_duration = self._get_video_duration(video_path)
        
        # 1. Görüntü analizi
        print("Görüntü analizi yapılıyor...")
        vision_result = self.vision_analyzer.analyze_video(video_path)
        
        # 2. Ses analizi
        print("Ses analizi yapılıyor...")
        audio_result = self.audio_analyzer.analyze_audio(video_path)
        
        # 3. İçerik analizi (eğer API anahtarı varsa)
        if self.content_analyzer:
            print("İçerik analizi yapılıyor...")
            content_result = self.content_analyzer.analyze_content(
                audio_result.transcription, subject_topic
            )
        else:
            # Varsayılan içerik sonucu
            content_result = ContentAnalysisResult(
                content_completeness_score=75.0,
                missing_topics=[],
                key_concepts=[],
                concept_density={},
                topic_flow_score=75.0,
                interaction_examples_count=5,
                educational_structure_score=70.0,
                overall_content_score=73.0,
                topic_heatmap=[]
            )
        
        # 4. Genel skorları hesapla
        scores = self._calculate_overall_scores(vision_result, audio_result, content_result)
        
        # 5. Öneriler oluştur
        recommendations = self._generate_recommendations(
            vision_result, audio_result, content_result
        )
        
        # 6. Sonuçları birleştir
        overall_result = OverallAnalysisResult(
            vision_analysis=vision_result,
            audio_analysis=audio_result,
            content_analysis=content_result,
            body_language_score=scores['body_language'],
            voice_score=scores['voice'],
            content_flow_score=scores['content_flow'],
            interaction_score=scores['interaction'],
            total_score=scores['total'],
            video_duration=video_duration,
            analysis_timestamp=datetime.now(),
            recommendations=recommendations
        )
        
        print("Analiz tamamlandı!")
        return overall_result
    
    def _get_video_duration(self, video_path: str) -> float:
        """Video süresini saniye cinsinden döndür"""
        import cv2
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return 0.0
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / fps if fps > 0 else 0.0
        
        cap.release()
        return duration
    
    def _calculate_overall_scores(self, vision: VisionAnalysisResult, 
                                 audio: AudioAnalysisResult, 
                                 content: ContentAnalysisResult) -> Dict[str, float]:
        """Genel skorları hesapla (100 üzerinden)"""
        
        # 1. Beden dili skoru (25 puan)
        body_language_score = (vision.overall_body_language_score / 100) * 25
        
        # 2. Ses skoru (25 puan)
        voice_score = (audio.overall_voice_score / 100) * 25
        
        # 3. İçerik akışı skoru (25 puan)
        content_flow_score = (
            (content.content_completeness_score * 0.4 + 
             content.topic_flow_score * 0.4 +
             content.educational_structure_score * 0.2) / 100
        ) * 25
        
        # 4. Etkileşim skoru (25 puan)
        # Hem ses hem görüntüdeki etkileşim faktörlerini birleştir
        gesture_factor = min(25, vision.gesture_activity * 25)
        interaction_factor = min(25, content.interaction_examples_count * 2.5)
        interaction_score = (gesture_factor + interaction_factor) / 2
        
        # 5. Toplam skor
        total_score = body_language_score + voice_score + content_flow_score + interaction_score
        
        return {
            'body_language': round(body_language_score, 1),
            'voice': round(voice_score, 1),
            'content_flow': round(content_flow_score, 1),
            'interaction': round(interaction_score, 1),
            'total': round(total_score, 1)
        }
    
    def _generate_recommendations(self, vision: VisionAnalysisResult,
                                audio: AudioAnalysisResult,
                                content: ContentAnalysisResult) -> list:
        """Analiz sonuçlarına göre öneriler oluştur"""
        
        recommendations = []
        
        # Beden dili önerileri
        if vision.eye_contact_percentage < 60:
            recommendations.append("👁️ Kamerayla göz teması kurmaya odaklanın. %60'ın altında göz teması tespit edildi.")
        
        if vision.posture_score < 0.7:
            recommendations.append("🏃‍♂️ Dik duruş sergileyin. Omuzlarınızı düz tutun ve güvenli görünün.")
        
        if vision.fidgeting_count > 10:
            recommendations.append("✋ Gereksiz hareketleri azaltın. Sakin ve kontrollü duruş sergileyin.")
        
        # Ses önerileri
        if audio.filler_words_percentage > 5:
            recommendations.append(f"🗣️ Dolgu kelimeleri azaltın (%{audio.filler_words_percentage:.1f} tespit edildi). Duraklamalar kullanmaya çalışın.")
        
        if audio.monotony_score > 0.7:
            recommendations.append("🎵 Ses tonunuzda daha fazla varyasyon yapın. Monoton konuşmaktan kaçının.")
        
        if audio.speech_rate < 120 or audio.speech_rate > 180:
            recommendations.append(f"⏱️ Konuşma hızınızı ayarlayın ({audio.speech_rate:.0f} kelime/dakika). İdeal: 120-180 kelime/dakika.")
        
        # İçerik önerileri
        if content.content_completeness_score < 80:
            recommendations.append("📚 İçerik bütünlüğünü artırın. Eksik konuları tamamlayın.")
        
        if content.interaction_examples_count < 5:
            recommendations.append("💡 Daha fazla örnek ve analoji kullanın. Öğrenci etkileşimini artırın.")
        
        if content.topic_flow_score < 75:
            recommendations.append("🔄 Konular arası geçişleri güçlendirin. Mantıksal sırayı gözden geçirin.")
        
        # İçerik analizörü varsa, AI önerilerini de ekle
        if self.content_analyzer and content.content_completeness_score < 90:
            try:
                ai_recommendations = self.content_analyzer.generate_recommendations(
                    content, audio.transcription
                )
                for rec in ai_recommendations[:3]:  # En fazla 3 AI önerisi
                    recommendations.append(f"🤖 {rec}")
            except:
                pass
        
        return recommendations[:10]  # Maksimum 10 öneri
    
    def create_performance_summary(self, result: OverallAnalysisResult) -> Dict[str, Any]:
        """Performans özeti oluştur"""
        
        # Güçlü ve zayıf yönleri belirle
        scores = {
            'Beden Dili': result.body_language_score,
            'Ses Kalitesi': result.voice_score,
            'İçerik Akışı': result.content_flow_score,
            'Etkileşim': result.interaction_score
        }
        
        # En yüksek ve en düşük skorları bul
        strengths = [k for k, v in scores.items() if v >= 20]  # 80% ve üzeri
        weaknesses = [k for k, v in scores.items() if v < 15]  # 60% altı
        
        # Skor kategorileri
        if result.total_score >= 85:
            performance_level = "Mükemmel"
            performance_emoji = "🏆"
        elif result.total_score >= 75:
            performance_level = "İyi"
            performance_emoji = "⭐"
        elif result.total_score >= 65:
            performance_level = "Orta"
            performance_emoji = "👍"
        else:
            performance_level = "Geliştirilmeli"
            performance_emoji = "📈"
        
        return {
            'performance_level': performance_level,
            'performance_emoji': performance_emoji,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'key_metrics': {
                'Göz Teması': f"%{result.vision_analysis.eye_contact_percentage:.1f}",
                'Konuşma Hızı': f"{result.audio_analysis.speech_rate:.0f} kelime/dk",
                'Dolgu Kelimeler': f"%{result.audio_analysis.filler_words_percentage:.1f}",
                'İçerik Bütünlüğü': f"%{result.content_analysis.content_completeness_score:.1f}"
            }
        } 