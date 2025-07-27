import gradio as gr
import asyncio
import os
import tempfile
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import json

from app.services.analysis_orchestrator import AnalysisOrchestrator, OverallAnalysisResult
from app.services.report_generator import ReportGenerator

# Global analyzer instance
analyzer = AnalysisOrchestrator()
report_generator = ReportGenerator()

def format_duration(seconds):
    """Saniyeyi dakika:saniye formatına çevir"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

def create_score_gauge(score, title, max_score=25):
    """Skor göstergesi oluştur"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        delta = {'reference': max_score * 0.8},
        gauge = {
            'axis': {'range': [None, max_score]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, max_score * 0.5], 'color': "lightgray"},
                {'range': [max_score * 0.5, max_score * 0.8], 'color': "yellow"},
                {'range': [max_score * 0.8, max_score], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_score * 0.9
            }
        }
    ))
    
    fig.update_layout(height=300, font={'size': 14})
    return fig

def create_comparison_chart(scores):
    """Skor karşılaştırma grafiği"""
    categories = list(scores.keys())
    values = list(scores.values())
    
    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            text=[f"{v:.1f}" for v in values],
            textposition='auto',
            marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        )
    ])
    
    fig.update_layout(
        title="Performans Kategorileri Karşılaştırması",
        yaxis_title="Puan (25 üzerinden)",
        xaxis_title="Kategoriler",
        height=400
    )
    
    return fig

def create_topic_heatmap(heatmap_data):
    """Konu yoğunluk haritası"""
    if not heatmap_data:
        return go.Figure().add_annotation(text="Veri mevcut değil", 
                                        xref="paper", yref="paper",
                                        x=0.5, y=0.5, showarrow=False)
    
    # Segment verilerini hazırla
    segments = []
    concepts = set()
    
    for segment in heatmap_data:
        segments.append(segment['segment_id'])
        concepts.update(segment['concept_scores'].keys())
    
    concepts = list(concepts)
    
    # Heatmap matrisi oluştur
    matrix = []
    for concept in concepts:
        row = []
        for segment in heatmap_data:
            score = segment['concept_scores'].get(concept, 0)
            row.append(score)
        matrix.append(row)
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=[f"Segment {i+1}" for i in segments],
        y=concepts,
        colorscale='Viridis'
    ))
    
    fig.update_layout(
        title="Konu Yoğunluk Haritası",
        xaxis_title="Video Segmentleri",
        yaxis_title="Anahtar Kavramlar",
        height=400
    )
    
    return fig

async def analyze_video(video_file, subject_topic, progress=gr.Progress()):
    """Ana video analiz fonksiyonu"""
    if video_file is None:
        return "Lütfen bir video dosyası yükleyin.", "", None, None, None, None, None, None
    
    try:
        progress(0.1, desc="Video yükleniyor...")
        
        # Geçici dosya oluştur
        temp_video_path = video_file  # Gradio zaten geçici dosya yolu veriyor
        
        progress(0.2, desc="Analiz başlatılıyor...")
        
        # Analizi çalıştır
        result = await analyzer.analyze_video(temp_video_path, subject_topic)
        
        progress(0.9, desc="Sonuçlar hazırlanıyor...")
        
        # Performans seviyesi belirleme
        def get_performance_level(score):
            if score >= 85:
                return "🏆 Mükemmel", "Olağanüstü sunum becerisi"
            elif score >= 75:
                return "⭐ İyi", "Güçlü performans, küçük iyileştirmeler"
            elif score >= 65:
                return "👍 Orta", "Gelişime açık alanlar mevcut"
            else:
                return "📈 Geliştirilmeli", "Önemli iyileştirmeler gerekli"
        
        performance_emoji, performance_desc = get_performance_level(result.total_score)
        
        # Ana skor göstergeleri
        total_score_gauge = create_score_gauge(result.total_score, "Toplam Performans", 100)
        body_language_gauge = create_score_gauge(result.body_language_score, "Beden Dili")
        voice_gauge = create_score_gauge(result.voice_score, "Ses Kalitesi")
        content_gauge = create_score_gauge(result.content_flow_score, "İçerik Akışı")
        
        # Karşılaştırma grafiği
        scores = {
            'Beden Dili': result.body_language_score,
            'Ses': result.voice_score,
            'İçerik': result.content_flow_score,
            'Etkileşim': result.interaction_score
        }
        comparison_chart = create_comparison_chart(scores)
        
        # Konu haritası
        heatmap_chart = create_topic_heatmap(result.content_analysis.topic_heatmap)
        
        # Detaylı analiz raporu
        detailed_report = f"""
        ## 📊 Detaylı Analiz Raporu
        
        ### 🎯 Genel Performans: {performance_emoji} {performance_desc}
        **Toplam Skor:** {result.total_score:.1f}/100
        
        ### 📈 Kategori Skorları
        - **Beden Dili:** {result.body_language_score:.1f}/25
        - **Ses Kalitesi:** {result.voice_score:.1f}/25  
        - **İçerik Akışı:** {result.content_flow_score:.1f}/25
        - **Etkileşim:** {result.interaction_score:.1f}/25
        
        ### 👁️ Beden Dili Analizi
        - **Göz Teması:** %{result.vision_analysis.eye_contact_percentage:.1f}
        - **Duruş Skoru:** {result.vision_analysis.posture_score:.1f}/100
        - **Jest Aktivitesi:** {result.vision_analysis.gesture_activity:.1f}/100
        - **Hareketlilik:** {result.vision_analysis.fidgeting_count} gereksiz hareket
        - **Yüz Yönü Değişimi:** {result.vision_analysis.face_direction_changes} kez
        
        ### 🎤 Ses Analizi  
        - **Konuşma Hızı:** {result.audio_analysis.speech_rate:.0f} kelime/dakika
        - **Dolgu Kelimeleri:** %{result.audio_analysis.filler_words_percentage:.1f} ({result.audio_analysis.filler_words_count} adet)
        - **Duraklama:** {result.audio_analysis.pause_count} duraklama, ortalama {result.audio_analysis.average_pause_duration:.1f}s
        - **Monotonluk Skoru:** {result.audio_analysis.monotony_score:.2f}/1.0
        - **Ses Tutarlılığı:** {result.audio_analysis.volume_consistency:.2f}/1.0
        
        ### 📚 İçerik Analizi
        - **İçerik Bütünlüğü:** %{result.content_analysis.content_completeness_score:.1f}
        - **Konu Akışı:** %{result.content_analysis.topic_flow_score:.1f}
        - **Eğitimsel Yapı:** %{result.content_analysis.educational_structure_score:.1f}
        - **Etkileşim Örnekleri:** {result.content_analysis.interaction_examples_count} adet
        - **Anahtar Kavramlar:** {len(result.content_analysis.key_concepts)} kavram
        
        ### 🎯 Anahtar Metrikler
        - **Video Süresi:** {format_duration(result.video_duration)}
        - **Transkript Uzunluğu:** {len(result.audio_analysis.transcription.split())} kelime
        - **Konuşma Hızı:** {result.audio_analysis.speech_rate:.1f} kelime/dakika
        - **Dolgu Kelime Oranı:** %{result.audio_analysis.filler_words_percentage:.1f}
        
        ### 📝 Transkript
        {result.audio_analysis.transcription[:500]}{'...' if len(result.audio_analysis.transcription) > 500 else ''}
        """
        
        # Öneriler listesi
        recommendations_text = "## 💡 Öneriler\n\n" + "\n".join([f"- {rec}" for rec in result.recommendations])
        
        progress(1.0, desc="Tamamlandı!")
        
        # Geçici dosyayı temizle (Gradio zaten hallediyor)
        # os.unlink(temp_video_path)  # Gradio kendi dosyalarını yönetir
        
        return (
            detailed_report,
            recommendations_text,
            total_score_gauge,
            comparison_chart,
            heatmap_chart,
            body_language_gauge,
            voice_gauge,
            content_gauge
        )
        
    except Exception as e:
        error_msg = f"❌ Analiz sırasında hata oluştu: {str(e)}"
        print(f"Hata: {e}")  # Debug için
        return error_msg, "", None, None, None, None, None, None

def create_interface():
    """Gradio arayüzü oluştur"""
    
    with gr.Blocks(title="🎓 EduView - AI Eğitim Analizi", theme=gr.themes.Soft()) as app:
        
        gr.Markdown("""
        # 🎓 EduView - AI ile Eğitim Video Analizi
        
        Eğitim videolarınızı yapay zeka ile analiz ederek sunum becerilerinizi geliştirin!
        
        📹 **Video yükleyin** → 🤖 **AI analiz eder** → 📊 **Detaylı rapor alın** → 📈 **Gelişin!**
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## 📤 Video Yükleme")
                
                video_input = gr.File(
                    label="Eğitim videosunu seçin",
                    file_types=[".mp4", ".avi", ".mov", ".mkv"],
                    file_count="single"
                )
                
                subject_input = gr.Textbox(
                    label="Konu/Ders Adı (Opsiyonel)",
                    placeholder="Örn: Matematik - Türev Konusu",
                    info="Bu bilgi içerik analizinde kullanılacak"
                )
                
                analyze_btn = gr.Button(
                    "🚀 Analizi Başlat", 
                    variant="primary",
                    size="lg"
                )
                
                gr.Markdown("""
                ### 📋 Analiz Edilen Özellikler:
                - 👁️ **Göz teması ve beden dili**
                - 🎤 **Ses tonu ve akıcılık**  
                - 📚 **İçerik bütünlüğü**
                - 💡 **Etkileşim ve örneklendirme**
                - 📊 **100 puanlık performans skoru**
                """)
            
            with gr.Column(scale=2):
                gr.Markdown("## 📊 Analiz Sonuçları")
                
                with gr.Tabs():
                    with gr.TabItem("🎯 Genel Performans"):
                        with gr.Row():
                            total_score_plot = gr.Plot(label="Toplam Performans")
                            comparison_plot = gr.Plot(label="Kategori Karşılaştırması")
                    
                    with gr.TabItem("📈 Detaylı Skorlar"):
                        with gr.Row():
                            body_language_plot = gr.Plot(label="Beden Dili")
                            voice_plot = gr.Plot(label="Ses Kalitesi")
                        with gr.Row():
                            content_plot = gr.Plot(label="İçerik Akışı")
                            heatmap_plot = gr.Plot(label="Konu Yoğunluk Haritası")
                    
                    with gr.TabItem("📋 Detaylı Rapor"):
                        detailed_output = gr.Markdown()
                    
                    with gr.TabItem("💡 Öneriler"):
                        recommendations_output = gr.Markdown()
        
        # Event handlers
        analyze_btn.click(
            fn=analyze_video,
            inputs=[video_input, subject_input],
            outputs=[
                detailed_output,
                recommendations_output, 
                total_score_plot,
                comparison_plot,
                heatmap_plot,
                body_language_plot,
                voice_plot,
                content_plot
            ],
            show_progress=True
        )
        
        # Footer
        gr.Markdown("""
        ---
        ### 🔧 Teknik Bilgiler
        - **Computer Vision:** MediaPipe, OpenCV ile beden dili analizi
        - **Speech Analysis:** Whisper, Librosa ile ses analizi  
        - **NLP:** Gemini AI ile içerik analizi
        - **Scoring:** 100 puanlık kapsamlı değerlendirme sistemi
        
        ### 📞 Destek
        Sorularınız için: [GitHub](https://github.com/yourusername/eduview) | [Dokümantasyon](https://docs.eduview.ai)
        """)
    
    return app

# Ana uygulama
if __name__ == "__main__":
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_error=True
    ) 