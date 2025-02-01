# Agaip - Super Power Agentic AI Framework

Agaip, AI modelleri, agentic AI, dinamik plugin yükleme ve agent yönetimi yapıları entegre edilebilen, asenkron, API odaklı ve çoklu dil/platform desteği sunan modern bir framework’üdür.

## Özellikler

- **API Odaklı:** RESTful API (FastAPI) ile tüm dillerden kolay entegrasyon (OpenAPI/Swagger).
- **Dinamik Plugin & Agent Yönetimi:** Yeni AI modelleri veya agent’lar yeniden başlatma gerektirmeden entegre edilebilir.
- **Asenkron İşlem & Görev İzleme:** Görevler Tortoise ORM (SQLite örneği) ile kaydedilir; asenkron olarak işlenir.
- **Güvenlik:** Token tabanlı erişim (prod ortamında JWT/OAuth2 önerilir).
- **DevOps Uyumlu:** Docker container, Kubernetes deployment dosyaları, CI/CD pipeline desteği.
- **Çoklu Dil/Platform Entegrasyonu:** Spring Boot, Django/Flask, Laravel, Go vb. ile uyumlu.

## Kurulum & Çalıştırma

### Yerel (Local) Çalışma
1. Gerekli paketleri yükleyin:
   ```bash
   pip install -r requirements.txt
