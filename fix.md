Setelah review menyeluruh terhadap seluruh codebase KURSORIN, ini rangkuman temuan dan update-nya:Setelah review menyeluruh terhadap semua file, ini temuan lengkapnya:Berikut semua perbaikan yang perlu dilakukan, diurutkan dari yang paling kritis:

---

**🔴 Bug #1 — `logger` tidak diimport di `app_window.py`**

Di baris `logger.info(f"Switched to scenario: {scenario}")`, tidak ada import `logger`. Ini akan crash saat scenario combo box diganti.

```python
# Tambahkan di bagian atas app_window.py
from loguru import logger
```

---

**🔴 Bug #2 — Pydantic v2 compatibility di `config.py`**

`requirements.txt` mengizinkan `pydantic>=1.10.0,<3.0.0` — jadi Pydantic v2 bisa terinstall dan akan crash karena dua hal:

```python
# SEBELUM (v1 style — crash di v2):
class Config:
    validate_assignment = True
    extra = "forbid"

def to_file(self, ...):
    data = self.dict()   # deprecated, crash di v2

# SESUDAH (kompatibel v1+v2):
model_config = {
    "validate_assignment": True,
    "extra": "forbid"
}

def to_file(self, ...):
    try:
        data = self.model_dump()   # v2
    except AttributeError:
        data = self.dict()         # v1 fallback
```

Atau pin dependensinya supaya konsisten:
```
# requirements.txt — pilih salah satu:
pydantic>=1.10.0,<2.0.0   # tetap v1
# atau
pydantic>=2.0.0,<3.0.0    # migrasi penuh ke v2
```

---

**🔴 Bug #3 — `ImageTk.PhotoImage` dibuat di worker thread**

Di `app_window.py`, method `_on_frame` dipanggil dari processing thread milik engine. Membuat `ImageTk` di luar main thread menyebabkan crash acak di Tkinter (khususnya di macOS dan Windows).

```python
def _on_frame(self, result: FrameResult):
    if result.frame is not None:
        vis_frame = self.overlay.draw(result.frame, result)
        rgb_frame = cv2.cvtColor(vis_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        # JANGAN buat ImageTk di sini — kirim ke main thread dulu
        self.root.after(0, self._update_video_label_from_image, img)

def _update_video_label_from_image(self, img: Image.Image):
    # ImageTk dibuat di main thread — aman
    imgtk = ImageTk.PhotoImage(image=img)
    self.video_label.configure(image=imgtk)
    self.video_label.image = imgtk
```

---

**🟡 Bug #4 — Duplicate assignment di `kursorin_engine.py`**

```python
# Baris 102-103 di kursorin_engine.py — hapus yang pertama:
self._click_detector: Optional[ClickDetector] = None
self._click_detector: Optional[ClickDetector] = None  # ← hapus ini
```

---

**🟡 Bug #5 — Dwell radius hardcoded di `click_detector.py`**

```python
# SEBELUM:
if dist > 0.02:

# SESUDAH — pakai config (konversi pixel ke normalized):
dwell_radius_normalized = self.config.click.dwell_radius_px / 1920.0  # approx
if dist > dwell_radius_normalized:
```

---

**🟡 Bug #6 — `timestamp` tidak pernah diisi di trackers**

`TrackerResult.timestamp` default `0.0` tapi tidak ada tracker yang mengisinya. Ini akan menyebabkan `OneEuroFilter` menghitung `dt=0` dan mengembalikan nilai lama terus-menerus sampai waktu pertama lewat.

```python
# Di head_tracker.py, eye_tracker.py, hand_tracker.py — tambahkan:
import time

return TrackerResult(
    valid=True,
    position=np.array([norm_x, norm_y]),
    confidence=1.0,
    timestamp=time.time(),   # ← ini yang kurang
    ...
)
```

---

**🔵 Bug #7 — File `kursorin/cli.py` tidak ada**

`__main__.py`, `setup.py`, dan `pyproject.toml` semuanya mereferensikan `kursorin.cli:main` tapi filenya tidak ada. `pip install -e .` akan berhasil tapi `kursorin-cli` command akan crash.

Buat file minimal:

```python
# kursorin/cli.py
"""KURSORIN CLI entry point."""
import click
from loguru import logger

@click.group()
def cli():
    """KURSORIN command line interface."""
    pass

@cli.command()
@click.option("--config", default=None, help="Path to config file")
def start(config):
    """Start KURSORIN in headless/CLI mode."""
    logger.info("CLI mode — starting KURSORIN")
    from kursorin.app import main
    main()

def main():
    cli()

if __name__ == "__main__":
    main()
```

---

**🟢 Performance — FaceMesh berjalan 2× per frame**

`HeadTracker` dan `EyeTracker` masing-masing memanggil `self.face_mesh.process(rgb_frame)` secara independen. Ini membuang ~25–30ms per frame. Arsitektur idealnya:

```
frame
  └─▶ FaceLandmarkProvider.process(frame)  ← 1× MediaPipe call
          ├─▶ HeadTracker.process(landmarks)
          └─▶ EyeTracker.process(landmarks)
```

Untuk sekarang solusi cepat: pass hasil dari `HeadTracker` ke `EyeTracker` lewat `FrameResult`, atau buat shared provider di engine. Ini prioritas medium tapi akan langsung terasa di hardware kelas menengah.

---

**Ringkasan prioritas pengerjaan:**

| Prioritas | Fix |
|---|---|
| 1 | Import `logger` di `app_window.py` |
| 2 | Pin atau fix Pydantic v1/v2 |
| 3 | `ImageTk` ke main thread |
| 4 | Buat `kursorin/cli.py` |
| 5 | Isi `timestamp` di semua trackers |
| 6 | Hapus duplicate `_click_detector` |
| 7 | Fix dwell radius pakai config |
| 8 | Shared FaceMesh provider |

//

# KURSORIN — Penjelasan & Full Update Plan

---

## Apa itu KURSORIN?

KURSORIN adalah sistem kontrol komputer tanpa sentuhan tangan yang hanya mengandalkan webcam biasa. Bayangkan kamu bisa menggerakkan kursor mouse, mengklik, dan berinteraksi dengan komputer hanya menggunakan gerakan kepala, arah pandangan mata, atau gerakan tangan — tanpa menyentuh mouse atau keyboard sama sekali.

Proyek ini dibuat oleh **Ardellio Satria Anindito**, kemungkinan besar sebagai proyek penelitian atau tugas akhir yang fokus pada **aksesibilitas** — membantu orang-orang dengan keterbatasan motorik agar tetap bisa menggunakan komputer.

Yang membuatnya istimewa adalah ia tidak memerlukan hardware mahal seperti eye tracker khusus seharga jutaan rupiah. Cukup webcam laptop biasa seharga 200 ribu pun bisa bekerja.

---

## Bagaimana cara kerjanya jika berjalan normal?

Bayangkan alurnya seperti ini dari awal sampai akhir:

**1. Kamera menangkap wajah dan tangan kamu secara real-time.** Setiap detik, 30 frame gambar diambil dari webcam.

**2. Tiga "mata" pelacak bekerja bersamaan** pada setiap frame tersebut:

- **Head Tracker** — membaca posisi wajah dan menghitung sudut kepala (miring kiri-kanan, atas-bawah). Jika kepala menoleh kanan sedikit, kursor bergerak ke kanan.
- **Eye Tracker** — membaca posisi iris mata menggunakan titik-titik landmark wajah yang sangat detail (468 titik di wajah). Ia tahu kemana kamu sedang memandang dan mendeteksi kedipan mata.
- **Hand Tracker** — membaca posisi jari-jari tangan. Jika jari telunjuk menunjuk, itu jadi arah kursor. Jika ibu jari dan telunjuk didekatkan (cubitan/pinch), itu jadi aksi klik.

**3. Fusion Module menggabungkan ketiga sinyal itu.** Tidak semua sinyal punya akurasi sama setiap saat. Misalnya kalau tangan sedang tidak terlihat di kamera, sistem akan lebih mengandalkan kepala dan mata. Fusion Module menghitung bobot masing-masing berdasarkan seberapa yakin setiap tracker pada hasilnya.

**4. Cursor Smoother menghaluskan gerakan.** Tanpa ini, kursor akan bergetar dan melompat-lompat karena deteksi kamera tidak sempurna. Filter matematika (One Euro Filter) memperhalus gerakan agar terasa natural seperti mouse biasa.

**5. Kursor di layar bergerak.** Sistem kemudian benar-benar menggerakkan mouse kursor di sistem operasi menggunakan PyAutoGUI — jadi semua aplikasi lain di komputer bisa dikontrol.

**6. Klik terdeteksi** lewat beberapa cara: kedipan mata sekali, menahan posisi diam selama 1 detik (dwell), atau cubitan jari.

**7. UI menampilkan preview** dari kamera dengan visualisasi titik-titik pelacakan, sehingga pengguna bisa melihat apa yang sedang dideteksi sistem.

---

## Kondisi proyek saat ini

Kode yang ada sudah membangun **fondasi yang sangat solid**. Semua komponen utama sudah ada dan tersambung satu sama lain. Namun ada beberapa bug kritis yang mencegah aplikasi berjalan sama sekali (seperti yang sudah diidentifikasi sebelumnya), dan beberapa fitur masih berupa placeholder yang belum berfungsi — seperti gesture tangan yang selalu mengembalikan "tidak ada gesture".

Analoginya seperti sebuah mobil yang sudah punya semua komponen — mesin, roda, setir, kursi — tapi ada beberapa kabel yang belum tersambung benar sehingga belum bisa dinyalakan.

---

## Full Plan: Update Besar KURSORIN

Rencana ini dibagi menjadi **4 Fase** yang berurutan. Setiap fase harus selesai sebelum masuk fase berikutnya karena saling bergantung.

---

### FASE 1 — Stabilisasi (Wajib Diselesaikan Dulu)
*Tujuan: Membuat aplikasi bisa berjalan tanpa crash*

Fase ini bukan menambah fitur baru, melainkan memperbaiki semua yang sudah ada agar benar-benar berfungsi. Tanpa fase ini, semua rencana berikutnya tidak ada artinya karena aplikasinya tidak bisa dibuka.

**Yang harus diselesaikan:**

Perbaikan kompatibilitas library Pydantic perlu menjadi prioritas pertama karena menyangkut sistem konfigurasi — tulang punggung seluruh aplikasi. Jika ini rusak, tidak ada satu pun pengaturan yang bisa dibaca dengan benar.

Masalah threading di tampilan video perlu diselesaikan karena ini menyebabkan crash acak yang sulit didiagnosis — kadang berjalan baik, kadang tiba-tiba mati tanpa pesan error yang jelas.

File CLI yang hilang perlu dibuat agar packaging dan instalasi bisa berfungsi penuh. Saat ini jika seseorang menginstall KURSORIN dan mencoba menjalankannya dari terminal, ia akan gagal karena file tersebut tidak ada.

Timestamp yang tidak pernah diisi di setiap tracker harus diperbaiki karena ini secara langsung merusak kualitas smoothing. Filter halus tidak bisa bekerja benar tanpa tahu kapan setiap data diambil.

**Hasil yang diharapkan di akhir Fase 1:** Aplikasi bisa dibuka, kamera aktif, preview muncul, kepala dan mata bisa menggerakkan kursor, dan tidak ada crash tiba-tiba.

---

### FASE 2 — Gesture dan Klik yang Berfungsi
*Tujuan: Semua metode klik dan gesture tangan benar-benar bekerja*

Saat ini gesture tangan adalah placeholder kosong. Pengguna tidak bisa mengklik menggunakan tangan karena sistem tidak pernah benar-benar mengenali gesture apapun.

**Yang perlu dibangun:**

Sistem pengenalan gesture dasar perlu dikembangkan dengan logika yang jelas dan terukur. Untuk setiap gesture, perlu ada definisi yang spesifik: jari mana yang harus terangkat, jari mana yang harus terlipat, dan berapa toleransi pergerakannya. Ini bukan pekerjaan kecil — gesture seperti "pointing" dan "pinch" terdengar sederhana tapi implementasinya butuh banyak penyesuaian agar akurat di berbagai ukuran dan posisi tangan.

Sistem deteksi klik perlu divalidasi secara menyeluruh. Saat ini dwell click (klik dengan cara diam di satu posisi) menggunakan angka yang hardcoded dan tidak mengikuti pengaturan yang ada di konfigurasi. Ini harus diperbaiki agar pengaturan dari UI benar-benar berpengaruh.

Feedback visual saat klik terdeteksi perlu ditambahkan. Pengguna harus tahu bahwa kliknya berhasil — misalnya animasi kecil atau perubahan warna di overlay. Tanpa ini, pengguna tidak tahu apakah mereka sudah mengklik atau belum.

**Hasil yang diharapkan di akhir Fase 2:** Pengguna bisa menggunakan KURSORIN untuk navigasi dasar — membuka aplikasi, mengklik tombol, menggulung halaman web.

---

### FASE 3 — Performa dan Kalibrasi yang Benar
*Tujuan: Membuat pengalaman yang cukup akurat dan responsif untuk penggunaan nyata*

Fase ini adalah tentang kualitas pengalaman. Aplikasi yang bekerja di Fase 1 dan 2 mungkin masih terasa kasar, lambat, atau tidak akurat.

**Yang perlu dibangun:**

Shared FaceMesh Provider adalah perubahan arsitektur terpenting di fase ini. Saat ini HeadTracker dan EyeTracker masing-masing menjalankan pemrosesan MediaPipe secara terpisah pada frame yang sama. Ini membuang waktu komputasi yang signifikan. Solusinya adalah membuat satu komponen terpusat yang menjalankan MediaPipe sekali per frame, lalu membagikan hasilnya ke semua tracker yang membutuhkan. Perubahan ini bisa memotong latensi hampir setengahnya pada konfigurasi default.

Sistem kalibrasi mata yang benar-benar fungsional perlu diimplementasikan. Saat ini ada UI kalibrasi yang bagus, tapi data yang dikumpulkan selama kalibrasi tidak benar-benar digunakan untuk menyesuaikan akurasi pelacakan mata. Ini perlu disambungkan sehingga setelah kalibrasi, akurasi pelacakan meningkat secara nyata.

Sistem penyimpanan dan pemuatan kalibrasi perlu dibuat. Pengguna tidak boleh harus kalibrasi ulang setiap kali membuka aplikasi. Data kalibrasi harus disimpan ke file dan dimuat otomatis saat aplikasi berikutnya dibuka.

Performance monitoring di UI perlu ditampilkan secara real-time — berapa FPS yang sedang berjalan, berapa latensi rata-rata, tracker mana yang sedang aktif. Ini penting untuk debugging dan juga memberi pengguna informasi apakah performa di perangkat mereka sudah baik.

**Hasil yang diharapkan di akhir Fase 3:** KURSORIN terasa cukup akurat dan responsif untuk digunakan dalam sesi beberapa jam tanpa terlalu melelahkan pengguna.

---

### FASE 4 — Fitur Baru dan Pemolesan
*Tujuan: Membuat KURSORIN layak dipresentasikan atau dipublikasikan*

Ini adalah fase yang paling menarik — menambahkan kemampuan baru yang memperluas apa yang bisa dilakukan KURSORIN.

**Fitur yang direkomendasikan untuk ditambahkan:**

**Scroll dan drag** — saat ini KURSORIN hanya bisa klik kiri, klik kanan, dan klik ganda. Untuk penggunaan nyata, pengguna perlu bisa menggulung halaman web dan memindahkan file. Scrolling bisa diimplementasikan lewat gesture tangan (misalnya dua jari bergerak naik-turun) atau gerakan kepala dengan modifier (misalnya tahan posisi sambil mengangguk).

**Mode profil pengguna** — orang yang menggunakan karena kelumpuhan tangan punya kebutuhan berbeda dari orang yang pakai karena tangan sedang kotor di dapur. Profil yang tersimpan akan memungkinkan pergantian konfigurasi dengan satu klik — sensitivitas berbeda, gesture berbeda, toleransi klik berbeda.

**Onboarding interaktif** — saat ini tidak ada panduan sama sekali untuk pengguna baru. Sebuah wizard setup yang berjalan pertama kali aplikasi dibuka — mengecek kamera, mengajarkan gesture dasar, dan menyelesaikan kalibrasi — akan sangat meningkatkan pengalaman pengguna baru terutama yang membutuhkan karena keterbatasan fisik.

**Statistik penggunaan** — mencatat berapa jam aplikasi digunakan, berapa klik yang dilakukan, akurasi rata-rata, dan lain-lain. Ini berguna untuk keperluan penelitian (jika ini memang proyek akademik) dan juga memberi pengguna rasa pencapaian.

**Dukungan multi-monitor** — saat ini sistem hanya mengetahui monitor utama. Pengguna dengan dua layar tidak bisa mengakses layar kedua.

**Hasil yang diharapkan di akhir Fase 4:** KURSORIN siap untuk demo publik, presentasi akademik, atau diunggah ke GitHub dengan dokumentasi yang lengkap.

---

## Perkiraan Waktu

| Fase | Estimasi Waktu | Catatan |
|---|---|---|
| Fase 1 — Stabilisasi | 3–5 hari | Wajib, tidak bisa dilewati |
| Fase 2 — Gesture & Klik | 1–2 minggu | Butuh banyak testing nyata |
| Fase 3 — Performa & Kalibrasi | 2–3 minggu | Yang paling teknis |
| Fase 4 — Fitur Baru | 2–4 minggu | Tergantung fitur mana yang dipilih |

Total estimasi dari awal sampai siap presentasi: **sekitar 6–10 minggu** jika dikerjakan serius, atau bisa lebih panjang jika sambil kuliah/kerja.

---

## Satu Hal yang Paling Penting

Dari semua yang ada di atas, satu pesan yang paling penting adalah: **jangan tambahkan fitur baru sebelum Fase 1 selesai.** Sangat mudah untuk tergiur menambahkan hal-hal keren sementara fondasi masih rapuh. Hasilnya justru akan makin sulit di-debug dan makin susah diperbaiki. Selesaikan bug kritis dulu, barulah bangun di atasnya.

---
