#!/usr/bin/env python3
"""
EduView - AI Educational Video Analysis
Startup Script

Bu script EduView uygulamasını başlatır.
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

def check_dependencies():
    """Gerekli bağımlılıkları kontrol et"""
    try:
        import gradio
        import fastapi
        import cv2
        print("✅ Ana bağımlılıklar yüklü")
        return True
    except ImportError as e:
        print(f"❌ Eksik bağımlılık: {e}")
        print("Lütfen 'pip install -r requirements.txt' komutunu çalıştırın")
        return False

def check_env_file():
    """Çevre değişkenleri dosyasını kontrol et"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env dosyası bulunamadı")
        print("env.example dosyasını .env olarak kopyalayın ve API anahtarlarınızı ekleyin")
        return False
    print("✅ .env dosyası mevcut")
    return True

def run_gradio():
    """Gradio arayüzünü başlat"""
    print("🚀 Gradio arayüzü başlatılıyor...")
    print("🌐 Tarayıcınızda http://localhost:7860 adresine gidin")
    try:
        subprocess.run([sys.executable, "gradio_app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Gradio başlatılırken hata: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Uygulama kapatıldı")
        return True

def run_fastapi():
    """FastAPI sunucusunu başlat"""
    print("🚀 FastAPI sunucusu başlatılıyor...")
    print("🌐 API dokümantasyonu: http://localhost:8000/docs")
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ FastAPI başlatılırken hata: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Sunucu kapatıldı")
        return True

def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description="EduView - AI Educational Video Analysis")
    parser.add_argument(
        "--mode", 
        choices=["gradio", "api"], 
        default="gradio",
        help="Başlatma modu: gradio (web arayüzü) veya api (FastAPI sunucu)"
    )
    parser.add_argument(
        "--skip-checks", 
        action="store_true",
        help="Bağımlılık kontrollerini atla"
    )
    
    args = parser.parse_args()
    
    print("🎓 EduView - AI Educational Video Analysis")
    print("=" * 50)
    
    # Kontroller
    if not args.skip_checks:
        if not check_dependencies():
            sys.exit(1)
        
        if not check_env_file():
            print("⚠️  Yine de devam etmek için --skip-checks kullanabilirsiniz")
            sys.exit(1)
    
    # Seçilen modu başlat
    if args.mode == "gradio":
        success = run_gradio()
    elif args.mode == "api":
        success = run_fastapi()
    
    if success:
        print("✅ Uygulama başarıyla çalıştı")
    else:
        print("❌ Uygulama başlatılamadı")
        sys.exit(1)

if __name__ == "__main__":
    main() 