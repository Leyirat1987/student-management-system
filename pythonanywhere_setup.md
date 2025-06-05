# PythonAnywhere-də yayımlamaq

1. www.pythonanywhere.com saytında hesab açın (pulsuz)
2. "Files" bölməsinə gedin
3. Bütün faylları yükləyin
4. "Consoles" bölməsində Bash console açın
5. Virtual environment yaradın:
   ```bash
   python3.10 -m venv mysite-virtualenv
   source mysite-virtualenv/bin/activate
   pip install -r requirements.txt
   ```

6. "Web" bölməsinə gedin
7. "Add a new web app" basın
8. Flask seçin
9. Source code path: /home/yourusername/
10. WSGI file-ı redaktə edin:
    ```python
    import sys
    path = '/home/yourusername'
    if path not in sys.path:
        sys.path.append(path)
    
    from app import app as application
    ```

11. Virtual env path: /home/yourusername/mysite-virtualenv
12. "Reload" basın 