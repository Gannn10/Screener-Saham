# 📈 Rumus-BSJP (Beli Sore Jual Pagi) Screener & Tracker

Repository ini berisi kumpulan script Python untuk melakukan *screening* dan *tracking* saham secara otomatis di Bursa Efek Indonesia (IHSG) menggunakan strategi **BSJP (Beli Sore Jual Pagi)**. 

Project ini dirancang untuk mempermudah analisis data pergerakan saham harian dan sudah terintegrasi dengan GitHub Actions untuk automasi eksekusi jadwal harian.

## 🚀 Fitur Utama

* **Screener Otomatis (`bsjp_auto.py`)**: Melakukan *screening* pada saham-saham potensial menjelang penutupan pasar untuk menemukan kandidat BSJP terbaik berdasarkan algoritma/rumus v6.
* **Tracker Portofolio & Harga (`bsjp_tracker.py`)**: Memantau pergerakan harga saham-saham yang masuk radar atau sudah dibeli untuk menentukan momentum *Take Profit* (TP) atau *Stop Loss* (SL) di pagi hari.
* **Auto-Execution (`bsjp_auto.py`)**: Script utama untuk menjalankan alur otomatisasi harian.
* **GitHub Actions Integration (`.github/workflows/bsjp.yml`)**: Workflow CI/CD yang dikonfigurasi untuk menjalankan *screener* dan *tracker* secara berkala (Cron Job) tanpa harus menyalakan komputer/server lokal.

## 🛠️ Persyaratan (Prerequisites)

Pastikan kamu sudah menginstal *dependencies* berikut sebelum menjalankan script secara lokal:
* Python 3.8+
* Pandas, NumPy (untuk analisis data)
* *Library API / Web Scraper* yang digunakan untuk mengambil data saham (sesuaikan dengan requirement)

## 💻 Cara Penggunaan Lokal

**Clone repository ini:**
   ```bash
   git clone [https://github.com/username/Rumus-Bsjp.git](https://github.com/username/Rumus-Bsjp.git)
   cd Rumus-Bsjp


Instal semua dependencies: 
Bash
pip install -r requirements.txt
Jalankan screener:

Bash
python bsjp_screener_v6.py
