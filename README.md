# 🎓 Şagird İdarəetmə Sistemi

Student Management System - Şagirdlərin məlumatlarının və PDF fayllarının idarə edilməsi üçün veb tətbiq.

## 🚀 Xüsusiyyətlər

- ✅ Şagird qeydiyyatı və məlumatların idarəsi
- ✅ PDF fayl yükləmə və yüklənmə
- ✅ Admin paneli
- ✅ UTIS kodu ilə giriş
- ✅ Excel-ə ixrac
- ✅ Axtarış və filtrləmə

## 🛠️ Texnologiyalar

- **Backend:** Python Flask
- **Database:** SQLite (development) / PostgreSQL (production)
- **Frontend:** HTML, CSS, JavaScript
- **File handling:** PDF upload/download

## 📋 Quraşdırma

1. **Repo-nu klonlayın:**
   ```bash
   git clone https://github.com/yourusername/student-management-system.git
   cd student-management-system
   ```

2. **Virtual environment yaradın:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

3. **Dependencies yükləyin:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database yaradın:**
   ```bash
   python app.py
   ```

5. **Tətbiqi işə salın:**
   ```bash
   python run_local.py
   ```

## 🌐 Deployment

Sistem Render.com platformasında deploy edilə bilər:

1. GitHub repo yaradın
2. Render.com-da hesab açın
3. Web Service yaradın
4. PostgreSQL database bağlayın

Ətraflı məlumat üçün `deployment_guide.md` faylına baxın.

## 📁 Fayl Strukturu

```
├── app.py              # Əsas Flask tətbiqi
├── config.py           # Konfiqurasiya parametrləri
├── requirements.txt    # Python dependencies
├── render.yaml         # Render.com deployment konfiqurasiyası
├── templates/          # HTML şablonları
├── uploads/           # Yüklənmiş PDF faylları
└── students.db       # SQLite database (development)
```

## 👨‍💻 İstifadə

1. **Admin giriş:** `/admin_login` - admin parolları ilə
2. **Şagird giriş:** Ana səhifədə UTIS kodu ilə
3. **PDF yükləmə:** Admin panelindən
4. **Məlumat ixracı:** Excel formatında

## 🔒 Təhlükəsizlik

- Admin parolları şifrələnmiş şəkildə saxlanılır
- File upload restrictions
- SQL injection protection
- XSS protection

## 📊 Sistemin imkanları

- **5000+ PDF** faylının saxlanılması
- **Çoxlu istifadəçi** dəstəyi
- **Performans optimizasiyası**
- **Backup və bərpa**

## 🤝 Contributing

1. Fork edin
2. Feature branch yaradın
3. Commit edin
4. Push edin
5. Pull Request göndərin

## 📄 License

MIT License

## 📞 Əlaqə

Suallarınız varsa issue açın və ya birbaşa əlaqə saxlayın. 