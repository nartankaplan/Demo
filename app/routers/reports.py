from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io
from datetime import datetime
from typing import Dict, Any

from ..services.report_generator import ReportGenerator
from ..services.analysis_orchestrator import OverallAnalysisResult

router = APIRouter()

# Global instance
report_generator = ReportGenerator()

@router.post("/generate-pdf/")
async def generate_pdf_report(analysis_data: Dict[Any, Any]):
    """Analiz sonuçlarından PDF raporu oluştur"""
    
    try:
        # Gelen JSON verilerinden OverallAnalysisResult nesnesi oluştur
        # Bu basitleştirilmiş bir yaklaşım - gerçekte daha kapsamlı validasyon gerekir
        
        # Mock data oluştur (gerçek implementasyonda database'den alınabilir)
        from ..services.vision_analyzer import VisionAnalysisResult
        from ..services.audio_analyzer import AudioAnalysisResult  
        from ..services.content_analyzer import ContentAnalysisResult
        
        # Örnek veri yapısı oluştur
        vision_result = VisionAnalysisResult(
            eye_contact_percentage=analysis_data.get('vision_analysis', {}).get('eye_contact_percentage', 75.0),
            posture_score=analysis_data.get('vision_analysis', {}).get('posture_score', 0.8),
            gesture_activity=analysis_data.get('vision_analysis', {}).get('gesture_activity', 0.6),
            fidgeting_count=analysis_data.get('vision_analysis', {}).get('fidgeting_count', 5),
            face_direction_changes=analysis_data.get('vision_analysis', {}).get('face_direction_changes', 10),
            overall_body_language_score=analysis_data.get('vision_analysis', {}).get('overall_body_language_score', 78.0)
        )
        
        audio_result = AudioAnalysisResult(
            transcription=analysis_data.get('audio_analysis', {}).get('transcription', "Örnek transkript..."),
            filler_words_count=analysis_data.get('audio_analysis', {}).get('filler_words_count', 3),
            filler_words_percentage=analysis_data.get('audio_analysis', {}).get('filler_words_percentage', 2.5),
            speech_rate=analysis_data.get('audio_analysis', {}).get('speech_rate', 150.0),
            pause_count=analysis_data.get('audio_analysis', {}).get('pause_count', 8),
            average_pause_duration=analysis_data.get('audio_analysis', {}).get('average_pause_duration', 1.2),
            pitch_variation=analysis_data.get('audio_analysis', {}).get('pitch_variation', 0.3),
            monotony_score=analysis_data.get('audio_analysis', {}).get('monotony_score', 0.4),
            volume_consistency=analysis_data.get('audio_analysis', {}).get('volume_consistency', 0.8),
            overall_voice_score=analysis_data.get('audio_analysis', {}).get('overall_voice_score', 82.0)
        )
        
        content_result = ContentAnalysisResult(
            content_completeness_score=analysis_data.get('content_analysis', {}).get('content_completeness_score', 85.0),
            missing_topics=analysis_data.get('content_analysis', {}).get('missing_topics', []),
            key_concepts=analysis_data.get('content_analysis', {}).get('key_concepts', ['matematik', 'türev', 'fonksiyon']),
            concept_density=analysis_data.get('content_analysis', {}).get('concept_density', {}),
            topic_flow_score=analysis_data.get('content_analysis', {}).get('topic_flow_score', 80.0),
            interaction_examples_count=analysis_data.get('content_analysis', {}).get('interaction_examples_count', 6),
            educational_structure_score=analysis_data.get('content_analysis', {}).get('educational_structure_score', 75.0),
            overall_content_score=analysis_data.get('content_analysis', {}).get('overall_content_score', 80.0),
            topic_heatmap=analysis_data.get('content_analysis', {}).get('topic_heatmap', [])
        )
        
        # OverallAnalysisResult nesnesi oluştur
        overall_result = OverallAnalysisResult(
            vision_analysis=vision_result,
            audio_analysis=audio_result,
            content_analysis=content_result,
            body_language_score=analysis_data.get('body_language_score', 20.0),
            voice_score=analysis_data.get('voice_score', 21.0),
            content_flow_score=analysis_data.get('content_flow_score', 20.0),
            interaction_score=analysis_data.get('interaction_score', 18.0),
            total_score=analysis_data.get('total_score', 79.0),
            video_duration=analysis_data.get('video_duration', 300.0),
            analysis_timestamp=datetime.now(),
            recommendations=analysis_data.get('recommendations', [])
        )
        
        # PDF oluştur
        pdf_bytes = report_generator.generate_report(overall_result)
        
        # PDF'i stream olarak döndür
        pdf_stream = io.BytesIO(pdf_bytes)
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=eduview_rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF raporu oluşturulurken hata oluştu: {str(e)}")

@router.get("/sample-report/")
async def generate_sample_report():
    """Örnek PDF raporu oluştur (demo amaçlı)"""
    
    try:
        from ..services.vision_analyzer import VisionAnalysisResult
        from ..services.audio_analyzer import AudioAnalysisResult  
        from ..services.content_analyzer import ContentAnalysisResult
        
        # Örnek veriler
        vision_result = VisionAnalysisResult(
            eye_contact_percentage=72.5,
            posture_score=0.85,
            gesture_activity=0.65,
            fidgeting_count=3,
            face_direction_changes=8,
            overall_body_language_score=81.0
        )
        
        audio_result = AudioAnalysisResult(
            transcription="Merhaba öğrenciler, bugün matematik dersimizde türev konusunu işleyeceğiz. Türev, bir fonksiyonun değişim hızını gösteren önemli bir kavramdır. Örnek olarak f(x) = x² fonksiyonunu ele alalım...",
            filler_words_count=5,
            filler_words_percentage=3.2,
            speech_rate=145.0,
            pause_count=12,
            average_pause_duration=1.8,
            pitch_variation=0.35,
            monotony_score=0.45,
            volume_consistency=0.78,
            overall_voice_score=79.0
        )
        
        content_result = ContentAnalysisResult(
            content_completeness_score=88.0,
            missing_topics=["türev kuralları örnekleri", "uygulama alanları"],
            key_concepts=["türev", "fonksiyon", "matematik", "değişim", "hız"],
            concept_density={"türev": 2.5, "fonksiyon": 1.8, "matematik": 1.2},
            topic_flow_score=83.0,
            interaction_examples_count=7,
            educational_structure_score=82.0,
            overall_content_score=84.0,
            topic_heatmap=[
                {"segment_id": 0, "start_word": 0, "end_word": 50, "concept_scores": {"türev": 0.1, "fonksiyon": 0.05}, "dominant_concept": "türev", "density_score": 0.15},
                {"segment_id": 1, "start_word": 50, "end_word": 100, "concept_scores": {"türev": 0.2, "matematik": 0.1}, "dominant_concept": "türev", "density_score": 0.3}
            ]
        )
        
        overall_result = OverallAnalysisResult(
            vision_analysis=vision_result,
            audio_analysis=audio_result,
            content_analysis=content_result,
            body_language_score=20.2,
            voice_score=19.8,
            content_flow_score=21.0,
            interaction_score=18.5,
            total_score=79.5,
            video_duration=420.0,  # 7 dakika
            analysis_timestamp=datetime.now(),
            recommendations=[
                "👁️ Kamerayla göz teması kurmaya odaklanın. %60'ın altında göz teması tespit edildi.",
                "🗣️ Dolgu kelimeleri azaltın (%3.2 tespit edildi). Duraklamalar kullanmaya çalışın.",
                "💡 Daha fazla örnek ve analoji kullanın. Öğrenci etkileşimini artırın.",
                "🔄 Konular arası geçişleri güçlendirin. Mantıksal sırayı gözden geçirin.",
                "🤖 Türev kuralları için daha fazla pratik örnek ekleyin"
            ]
        )
        
        # PDF oluştur
        pdf_bytes = report_generator.generate_report(overall_result)
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=eduview_ornek_rapor.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Örnek rapor oluşturulurken hata oluştu: {str(e)}")

@router.get("/report-template/")
async def get_report_template():
    """Rapor şablonu bilgilerini döndür"""
    return {
        "sections": [
            "Genel Bilgiler",
            "Performans Skorları", 
            "Beden Dili Analizi",
            "Ses Analizi",
            "İçerik Analizi",
            "İyileştirme Önerileri",
            "Video Transkripti"
        ],
        "supported_formats": ["PDF"],
        "customization_options": [
            "Logo ekleme",
            "Renk teması",
            "Bölüm seçimi",
            "Detay seviyesi"
        ]
    } 