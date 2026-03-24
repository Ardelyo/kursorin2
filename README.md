# 🎯 KURSORIN

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Sistem Interaksi Manusia-Komputer Berbasis Webcam yang Terjangkau Menggunakan Pelacakan Kepala, Tangan, dan Mata**

KURSORIN memungkinkan kontrol komputer tanpa sentuhan (hands-free) hanya dengan menggunakan webcam standar. Sangat cocok untuk pengguna dengan keterbatasan motorik, skenario di mana tangan sedang sibuk, atau siapa saja yang mencari metode input alternatif.

## ✨ Fitur

- **🎯 Pelacakan Multi-Modal**: Estimasi pose kepala, gestur tangan, dan tatapan mata.
- **🔄 Fusi Adaptif**: Kombinasi cerdas dari berbagai modalitas pelacakan.
- **👆 Berbagai Metode Klik**: Kedipan mata, diam di tempat (dwell), cubitan jari (pinch), gestur mulut.
- **⚡ Performa Real-Time**: Latensi rendah (~45ms) pada perangkat keras kelas menengah.
- **🎨 UI yang Dapat Disesuaikan**: Antarmuka modern dengan tema gelap/terang.
- **♿ Fokus Aksesibilitas**: Dirancang khusus untuk pengguna dengan gangguan motorik.
- **💰 Biaya Perangkat Keras Nol**: Bekerja dengan webcam standar apa pun.

## 🚀 Mulai Cepat

### Instalasi

```bash
# Clone repositori
git clone https://github.com/yourusername/kursorin.git
cd kursorin

# Buat virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# Instal dependensi
pip install -r requirements.txt

# Jalankan KURSORIN
python -m kursorin
```

### Penggunaan Dasar

```python
from kursorin import Kursorin

# Inisialisasi dengan pengaturan default
app = Kursorin()

# Mulai pelacakan
app.start()
```

## 📁 Struktur Repositori

- `kursorin/`: Kode sumber utama mesin dan TUI Kursorin.
  - `assets/models/`: Lokasi model pra-terlatih `.task` (Face dan Hand Landmarker).
- `benchmarks/`: Skrip dan hasil pengujian performa (`benchmark.py`).
- `docs/`: Dokumentasi tambahan, referensi perbaikan (`fix.md`), dan panduan lainnya.
- `tests/`: Pengujian unit dan integrasi.

## 📋 Persyaratan Sistem

**Minimum:**
- CPU: Intel Core i3 (Gen 8) atau AMD Ryzen 3
- RAM: 4 GB
- Webcam: 720p, 30 fps
- OS: Windows 10, macOS 10.14, atau Ubuntu 18.04
- Python 3.8+

**Direkomendasikan:**
- CPU: Intel Core i5 (Gen 10) atau AMD Ryzen 5
- RAM: 8 GB
- Webcam: 1080p, 30 fps dengan autofokus

## 🎮 Kontrol

| Gestur | Aksi |
|--------|------|
| Tunjuk (jari telunjuk) | Gerakkan kursor |
| Cubit (jempol + telunjuk) | Klik kiri |
| Cubit ganda | Klik ganda |
| Kedipan mata | Klik (dapat dikonfigurasi) |
| Dwell (tahan posisi) | Klik |
| Telapak tangan terbuka | Jeda pelacakan |

## 🤝 Berkontribusi

Kami menyambut kontribusi! Silakan lihat CONTRIBUTING.md untuk panduan.

## 📄 Lisensi

Proyek ini dilisensikan di bawah Lisensi MIT - lihat file LICENSE.

## 🙏 Ucapan Terima Kasih

- Tim MediaPipe untuk framework mereka yang luar biasa.
- Komunitas OpenCV.
- Semua partisipan studi.

---
Dibuat dengan ❤️ untuk aksesibilitas.
