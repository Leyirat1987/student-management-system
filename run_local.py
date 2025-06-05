from app import app
import os

if __name__ == '__main__':
    # Get your local IP address
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"Sayt işə salınır...")
    print(f"Yerli ünvan: http://127.0.0.1:5000")
    print(f"Şəbəkə ünvanı: http://{local_ip}:5000")
    print("Dayandırmaq üçün Ctrl+C basın")
    
    # Run the app accessible from network
    app.run(host='0.0.0.0', port=5000, debug=False) 