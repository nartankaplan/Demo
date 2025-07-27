#!/usr/bin/env python3
"""
EduView Installation Test Script

Bu script EduView kurulumunu test eder ve potansiyel sorunları tespit eder.
"""

import sys
import os
import subprocess
from pathlib import Path

def test_python_version():
    """Python versiyonunu test et"""
    print("🐍 Python versiyonu kontrol ediliyor...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} (uyumlu)")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (Python 3.8+ gerekli)")
        return False

def test_required_packages():
    """Gerekli paketleri test et"""
    print("📦 Gerekli paketler kontrol ediliyor...")
    
    packages = {
        'gradio': 'Gradio web arayüzü',
        'fastapi': 'FastAPI web framework',
        'uvicorn': 'ASGI sunucu',
        'cv2': 'OpenCV görüntü işleme',
        'mediapipe': 'MediaPipe AI framework',
        'whisper': 'OpenAI Whisper ses tanıma',
        'google.generativeai': 'Google Gemini AI',
        'reportlab': 'PDF oluşturma',
        'plotly': 'Grafik kütüphanesi',
        'numpy': 'Numerical computing',
        'pandas': 'Veri analizi',
    }
    
    missing_packages = []
    
    for package, description in packages.items():
        try:
            if package == 'cv2':
                import cv2
            else:
                __import__(package)
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"❌ {package} - {description} (eksik)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Eksik paketler: {', '.join(missing_packages)}")
        print("Eksik paketleri yüklemek için: pip install -r requirements.txt")
        return False
    else:
        print("✅ Tüm gerekli paketler yüklü")
        return True

def test_file_structure():
    """Dosya yapısını test et"""
    print("📁 Dosya yapısı kontrol ediliyor...")
    
    required_files = [
        'gradio_app.py',
        'requirements.txt',
        'run.py',
        'app/__init__.py',
        'app/main.py',
        'app/core/config.py',
        'app/services/__init__.py',
        'app/services/vision_analyzer.py',
        'app/services/audio_analyzer.py',
        'app/services/content_analyzer.py',
        'app/services/analysis_orchestrator.py',
        'app/services/report_generator.py',
        'app/routers/__init__.py',
        'app/routers/analysis.py',
        'app/routers/reports.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (eksik)")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Eksik dosyalar: {', '.join(missing_files)}")
        return False
    else:
        print("✅ Tüm gerekli dosyalar mevcut")
        return True

def test_environment():
    """Çevre değişkenlerini test et"""
    print("🔧 Çevre değişkenleri kontrol ediliyor...")
    
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env dosyası mevcut")
        
        # .env dosyasını oku
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        if 'GEMINI_API_KEY' in env_content:
            print("✅ GEMINI_API_KEY tanımlı")
        else:
            print("⚠️  GEMINI_API_KEY tanımlı değil (içerik analizi çalışmayabilir)")
        
        return True
    else:
        print("⚠️  .env dosyası bulunamadı")
        print("env.example dosyasını .env olarak kopyalayın")
        return False

def test_import_modules():
    """Ana modülleri import etmeyi test et"""
    print("🔄 Modül importları test ediliyor...")
    
    try:
        from app.services.vision_analyzer import VisionAnalyzer
        print("✅ VisionAnalyzer import edildi")
    except Exception as e:
        print(f"❌ VisionAnalyzer import hatası: {e}")
        return False
    
    try:
        from app.services.audio_analyzer import AudioAnalyzer
        print("✅ AudioAnalyzer import edildi")
    except Exception as e:
        print(f"❌ AudioAnalyzer import hatası: {e}")
        return False
    
    try:
        from app.services.analysis_orchestrator import AnalysisOrchestrator
        print("✅ AnalysisOrchestrator import edildi")
    except Exception as e:
        print(f"❌ AnalysisOrchestrator import hatası: {e}")
        return False
    
    return True

def test_system_requirements():
    """Sistem gereksinimlerini test et"""
    print("💻 Sistem gereksinimleri kontrol ediliyor...")
    
    # FFmpeg kontrolü
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg yüklü")
        else:
            print("⚠️  FFmpeg bulunamadı (video işleme için gerekli)")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  FFmpeg bulunamadı (video işleme için gerekli)")
    
    return True

def main():
    """Ana test fonksiyonu"""
    print("🎓 EduView Installation Test")
    print("=" * 50)
    
    tests = [
        ("Python Version", test_python_version),
        ("Required Packages", test_required_packages),
        ("File Structure", test_file_structure),
        ("Environment", test_environment),
        ("Module Imports", test_import_modules),
        ("System Requirements", test_system_requirements),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test hatası: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print("📊 Test Sonuçları")
    print(f"✅ Başarılı: {passed}")
    print(f"❌ Başarısız: {failed}")
    
    if failed == 0:
        print("\n🎉 Tüm testler başarılı! EduView kullanıma hazır.")
        print("Başlatmak için: python run.py")
    else:
        print(f"\n⚠️  {failed} test başarısız. Lütfen sorunları giderin.")
        print("Kurulum talimatları için README.md dosyasını inceleyin.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 