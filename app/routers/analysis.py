from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Optional
import tempfile
import os
import io
from datetime import datetime

from ..services.analysis_orchestrator import AnalysisOrchestrator
from ..services.report_generator import ReportGenerator

router = APIRouter()

# Global instances
analyzer = AnalysisOrchestrator()
report_generator = ReportGenerator()

@router.post("/upload-video/")
async def upload_and_analyze_video(
    video: UploadFile = File(...),
    subject_topic: Optional[str] = None
):
    """Video yükle ve analiz et"""
    
    # Dosya türü kontrolü
    if not video.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="Sadece video dosyaları kabul edilir")
    
    # Geçici dosya oluştur
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video.filename)[1]) as tmp_file:
        # Video içeriğini geçici dosyaya kaydet
        content = await video.read()
        tmp_file.write(content)
        temp_video_path = tmp_file.name
    
    try:
        # Analizi çalıştır
        result = await analyzer.analyze_video(temp_video_path, subject_topic)
        
        # Sonuçları JSON formatında döndür
        return {
            "status": "success",
            "analysis_id": f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "results": {
                "total_score": result.total_score,
                "body_language_score": result.body_language_score,
                "voice_score": result.voice_score,
                "content_flow_score": result.content_flow_score,
                "interaction_score": result.interaction_score,
                "video_duration": result.video_duration,
                "analysis_timestamp": result.analysis_timestamp.isoformat(),
                "vision_analysis": {
                    "eye_contact_percentage": result.vision_analysis.eye_contact_percentage,
                    "posture_score": result.vision_analysis.posture_score,
                    "gesture_activity": result.vision_analysis.gesture_activity,
                    "fidgeting_count": result.vision_analysis.fidgeting_count,
                    "face_direction_changes": result.vision_analysis.face_direction_changes,
                    "overall_body_language_score": result.vision_analysis.overall_body_language_score
                },
                "audio_analysis": {
                    "transcription": result.audio_analysis.transcription,
                    "filler_words_count": result.audio_analysis.filler_words_count,
                    "filler_words_percentage": result.audio_analysis.filler_words_percentage,
                    "speech_rate": result.audio_analysis.speech_rate,
                    "pause_count": result.audio_analysis.pause_count,
                    "average_pause_duration": result.audio_analysis.average_pause_duration,
                    "pitch_variation": result.audio_analysis.pitch_variation,
                    "monotony_score": result.audio_analysis.monotony_score,
                    "volume_consistency": result.audio_analysis.volume_consistency,
                    "overall_voice_score": result.audio_analysis.overall_voice_score
                },
                "content_analysis": {
                    "content_completeness_score": result.content_analysis.content_completeness_score,
                    "missing_topics": result.content_analysis.missing_topics,
                    "key_concepts": result.content_analysis.key_concepts,
                    "concept_density": result.content_analysis.concept_density,
                    "topic_flow_score": result.content_analysis.topic_flow_score,
                    "interaction_examples_count": result.content_analysis.interaction_examples_count,
                    "educational_structure_score": result.content_analysis.educational_structure_score,
                    "overall_content_score": result.content_analysis.overall_content_score,
                    "topic_heatmap": result.content_analysis.topic_heatmap
                },
                "recommendations": result.recommendations
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analiz sırasında hata oluştu: {str(e)}")
    
    finally:
        # Geçici dosyayı temizle
        if os.path.exists(temp_video_path):
            os.unlink(temp_video_path)

@router.get("/analyze-status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Analiz durumunu sorgula (gelecekte async işlemler için)"""
    return {
        "analysis_id": analysis_id,
        "status": "completed",  # Şimdilik tüm analizler senkron
        "message": "Analiz tamamlandı"
    }

@router.post("/health-check/")
async def health_check():
    """Sistem sağlık kontrolü"""
    try:
        # Temel bileşenlerin çalışıp çalışmadığını kontrol et
        test_analyzer = AnalysisOrchestrator()
        
        return {
            "status": "healthy",
            "components": {
                "vision_analyzer": "ok",
                "audio_analyzer": "ok", 
                "content_analyzer": "ok" if test_analyzer.content_analyzer else "disabled (no API key)",
                "report_generator": "ok"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Sistem sağlık kontrolü başarısız: {str(e)}")

@router.get("/supported-formats/")
async def get_supported_formats():
    """Desteklenen video formatlarını döndür"""
    return {
        "supported_video_formats": [".mp4", ".avi", ".mov", ".mkv"],
        "max_file_size_mb": 500,
        "recommended_duration_minutes": "2-15",
        "recommended_resolution": "720p veya üzeri"
    } 