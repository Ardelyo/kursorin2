"""
KURSORIN Internationalization (i18n)

Supports Bahasa Indonesia (id) and English (en).
Language is auto-detected from config or system locale.
"""

from __future__ import annotations

import locale
import os
from pathlib import Path
from typing import Dict, Optional


# ─── String Tables ────────────────────────────────────────────────────────────

_STRINGS: Dict[str, Dict[str, str]] = {
    # ── CLI ───────────────────────────────────────────────────────────────
    "cli.description": {
        "en": "KURSORIN — Webcam-based hands-free computer control.",
        "id": "KURSORIN — Kontrol komputer tanpa sentuhan berbasis webcam.",
    },
    "cli.subtitle": {
        "en": "Webcam-Based Human-Computer Interaction System",
        "id": "Sistem Interaksi Manusia-Komputer Berbasis Webcam",
    },
    "cli.version_line": {
        "en": "v1.2.9 · Hands-free cursor control via head, hand & eye tracking",
        "id": "v1.2.9 · Kontrol kursor tanpa sentuhan melalui pelacakan kepala, tangan & mata",
    },
    "cli.cmd.start": {
        "en": "Start tracking",
        "id": "Mulai pelacakan",
    },
    "cli.cmd.config": {
        "en": "Show or edit configuration",
        "id": "Tampilkan atau ubah konfigurasi",
    },
    "cli.cmd.calibrate": {
        "en": "Run eye calibration",
        "id": "Jalankan kalibrasi mata",
    },
    "cli.cmd.status": {
        "en": "Show system status",
        "id": "Tampilkan status sistem",
    },
    "cli.cmd.doctor": {
        "en": "Diagnose system health",
        "id": "Diagnosis kesehatan sistem",
    },
    "cli.cmd.gui": {
        "en": "Launch GUI application",
        "id": "Buka aplikasi GUI",
    },
    "cli.cmd.lang": {
        "en": "Switch language (en/id)",
        "id": "Ganti bahasa (en/id)",
    },
    "cli.cmd.info": {
        "en": "Show detailed system info",
        "id": "Tampilkan info sistem lengkap",
    },
    "cli.cmd.update": {
        "en": "Check and pull updates via git",
        "id": "Cek dan unduh pembaruan melalui git",
    },
    "cli.quick_ref": {
        "en": "Quick Reference",
        "id": "Panduan Cepat",
    },
    "cli.run_help": {
        "en": "Run [bold]kursorin <command> --help[/bold] for more info.",
        "id": "Jalankan [bold]kursorin <perintah> --help[/bold] untuk info lebih.",
    },
    "cli.commands": {
        "en": "Commands",
        "id": "Perintah",
    },

    # ── Start ─────────────────────────────────────────────────────────────
    "start.loading_config": {
        "en": "Loading configuration...",
        "id": "Memuat konfigurasi...",
    },
    "start.starting": {
        "en": "Starting engine...",
        "id": "Memulai mesin...",
    },
    "start.press_ctrl_c": {
        "en": "Press Ctrl+C to stop",
        "id": "Tekan Ctrl+C untuk berhenti",
    },
    "start.stopped": {
        "en": "Stopped by user.",
        "id": "Dihentikan oleh pengguna.",
    },
    "start.engine_error": {
        "en": "Engine error",
        "id": "Kesalahan mesin",
    },
    "start.config_summary": {
        "en": "Configuration Summary",
        "id": "Ringkasan Konfigurasi",
    },
    "start.live_dashboard": {
        "en": "Live Dashboard",
        "id": "Dasbor Langsung",
    },
    "start.help_desc": {
        "en": "Start the KURSORIN tracking engine.",
        "id": "Mulai mesin pelacakan KURSORIN.",
    },

    # ── Config ────────────────────────────────────────────────────────────
    "config.title": {
        "en": "KURSORIN Configuration",
        "id": "Konfigurasi KURSORIN",
    },
    "config.config_file": {
        "en": "Config file",
        "id": "File konfigurasi",
    },
    "config.reset_ok": {
        "en": "Configuration reset to defaults",
        "id": "Konfigurasi direset ke default",
    },
    "config.set_ok": {
        "en": "Set",
        "id": "Diatur",
    },
    "config.help_desc": {
        "en": "Show or edit configuration.",
        "id": "Tampilkan atau ubah konfigurasi.",
    },

    # ── Status ────────────────────────────────────────────────────────────
    "status.title": {
        "en": "System Status",
        "id": "Status Sistem",
    },
    "status.component": {
        "en": "Component",
        "id": "Komponen",
    },
    "status.available": {
        "en": "Available",
        "id": "Tersedia",
    },
    "status.not_found": {
        "en": "Not found",
        "id": "Tidak ditemukan",
    },
    "status.installed": {
        "en": "Installed",
        "id": "Terpasang",
    },
    "status.missing": {
        "en": "Missing",
        "id": "Tidak ada",
    },
    "status.not_created": {
        "en": "Not created",
        "id": "Belum dibuat",
    },
    "status.not_calibrated": {
        "en": "Not calibrated",
        "id": "Belum dikalibrasi",
    },
    "status.saved": {
        "en": "Saved",
        "id": "Tersimpan",
    },
    "status.stopped": {
        "en": "All matching processes terminated.",
        "id": "Semua proses yang cocok telah dihentikan.",
    },
    "status.not_running": {
        "en": "No KURSORIN process found running.",
        "id": "Tidak ada proses KURSORIN yang berjalan.",
    },

    # ── Doctor ────────────────────────────────────────────────────────────
    "doctor.running": {
        "en": "Running diagnostics...",
        "id": "Menjalankan diagnostik...",
    },
    "doctor.all_passed": {
        "en": "All {n} checks passed.",
        "id": "Semua {n} pemeriksaan berhasil.",
    },
    "doctor.system_ready": {
        "en": "Your system is ready to run KURSORIN.",
        "id": "Sistem Anda siap menjalankan KURSORIN.",
    },
    "doctor.health_check": {
        "en": "Health Check",
        "id": "Pemeriksaan Kesehatan",
    },
    "doctor.issues_found": {
        "en": "Issues Found",
        "id": "Masalah Ditemukan",
    },
    "doctor.passed_n": {
        "en": "{passed}/{total} checks passed.",
        "id": "{passed}/{total} pemeriksaan berhasil.",
    },
    "doctor.recommended_fixes": {
        "en": "Recommended fixes",
        "id": "Perbaikan yang disarankan",
    },
    "doctor.camera_ok": {
        "en": "Camera accessible",
        "id": "Kamera dapat diakses",
    },
    "doctor.camera_fail": {
        "en": "Camera not accessible",
        "id": "Kamera tidak dapat diakses",
    },
    "doctor.data_dir_ok": {
        "en": "Data directory exists",
        "id": "Direktori data ada",
    },
    "doctor.data_dir_missing": {
        "en": "Data directory missing (will be created on first run)",
        "id": "Direktori data belum ada (akan dibuat saat pertama kali dijalankan)",
    },
    "doctor.help_desc": {
        "en": "Diagnose system health and fix common issues.",
        "id": "Diagnosis kesehatan sistem dan perbaiki masalah umum.",
    },

    # ── Calibrate ─────────────────────────────────────────────────────────
    "calibrate.starting": {
        "en": "Starting calibration...",
        "id": "Memulai kalibrasi...",
    },
    "calibrate.points": {
        "en": "Calibration points",
        "id": "Titik kalibrasi",
    },
    "calibrate.instruction": {
        "en": "A fullscreen calibration window will open.\nLook at each dot until it moves to the next position.",
        "id": "Jendela kalibrasi layar penuh akan terbuka.\nLihat setiap titik sampai berpindah ke posisi berikutnya.",
    },
    "calibrate.complete": {
        "en": "Calibration complete and saved.",
        "id": "Kalibrasi selesai dan tersimpan.",
    },
    "calibrate.failed": {
        "en": "Calibration failed",
        "id": "Kalibrasi gagal",
    },

    # ── GUI labels ────────────────────────────────────────────────────────
    "gui.brand": {
        "en": "KURSORIN",
        "id": "KURSORIN",
    },
    "gui.subtitle": {
        "en": "Hands-free Control",
        "id": "Kontrol Tanpa Sentuhan",
    },
    "gui.home": {
        "en": "Home",
        "id": "Beranda",
    },
    "gui.settings": {
        "en": "Settings",
        "id": "Pengaturan",
    },
    "gui.dashboard": {
        "en": "Dashboard",
        "id": "Dasbor",
    },
    "gui.start_tracking": {
        "en": "▶  Start Tracking",
        "id": "▶  Mulai Pelacakan",
    },
    "gui.stop_tracking": {
        "en": "⏹  Stop Tracking",
        "id": "⏹  Hentikan Pelacakan",
    },
    "gui.calibrate": {
        "en": "🎯  Calibrate",
        "id": "🎯  Kalibrasi",
    },
    "gui.scenario": {
        "en": "Scenario",
        "id": "Skenario",
    },
    "gui.ready": {
        "en": "Ready",
        "id": "Siap",
    },
    "gui.stopped": {
        "en": "Stopped",
        "id": "Dihentikan",
    },
    "gui.tracking_active": {
        "en": "● Tracking active",
        "id": "● Pelacakan aktif",
    },
    "gui.start_first": {
        "en": "Start tracking first",
        "id": "Mulai pelacakan terlebih dahulu",
    },
    "gui.calib_complete": {
        "en": "✓ Calibration complete",
        "id": "✓ Kalibrasi selesai",
    },
    "gui.settings_saved": {
        "en": "✓ Settings saved",
        "id": "✓ Pengaturan tersimpan",
    },
    "gui.camera_preview": {
        "en": "Camera preview will appear here\nPress Start Tracking to begin",
        "id": "Pratinjau kamera akan muncul di sini\nTekan Mulai Pelacakan untuk memulai",
    },
    "gui.error": {
        "en": "Error",
        "id": "Kesalahan",
    },
    "gui.limited_control": {
        "en": "Limited Control",
        "id": "Kontrol Terbatas",
    },
    "gui.admin_warning": {
        "en": "Admin Rights Required",
        "id": "Akses Admin Diperlukan",
    },
    "gui.admin_tooltip": {
        "en": "Administrative privileges are required on Windows to control system windows like Task Manager and UAC prompts.",
        "id": "Hak akses administrator diperlukan pada Windows untuk dapat mengontrol jendela sistem seperti Task Manager dan jendela UAC.",
    },

    # ── Settings panel ────────────────────────────────────────────────────
    "settings.title": {
        "en": "⚙  Settings",
        "id": "⚙  Pengaturan",
    },
    "settings.save": {
        "en": "Save Settings",
        "id": "Simpan Pengaturan",
    },
    "settings.reset": {
        "en": "Reset Defaults",
        "id": "Reset ke Default",
    },
    "settings.tracking": {
        "en": "Tracking",
        "id": "Pelacakan",
    },
    "settings.click": {
        "en": "Click",
        "id": "Klik",
    },
    "settings.camera": {
        "en": "Camera",
        "id": "Kamera",
    },
    "settings.performance": {
        "en": "Performance",
        "id": "Kinerja",
    },
    "settings.appearance": {
        "en": "Appearance",
        "id": "Tampilan",
    },
    "settings.head_tracking": {
        "en": "Head Tracking",
        "id": "Pelacakan Kepala",
    },
    "settings.eye_tracking": {
        "en": "Eye Tracking",
        "id": "Pelacakan Mata",
    },
    "settings.hand_tracking": {
        "en": "Hand Tracking",
        "id": "Pelacakan Tangan",
    },
    "settings.sensitivity_x": {
        "en": "Head Sensitivity X",
        "id": "Sensitivitas Kepala X",
    },
    "settings.sensitivity_y": {
        "en": "Head Sensitivity Y",
        "id": "Sensitivitas Kepala Y",
    },
    "settings.smoothing": {
        "en": "Smoothing",
        "id": "Penghalusan",
    },
    "settings.invert_x": {
        "en": "Invert X",
        "id": "Balik X",
    },
    "settings.invert_y": {
        "en": "Invert Y",
        "id": "Balik Y",
    },
    "settings.blink_click": {
        "en": "Blink Click",
        "id": "Klik Kedip",
    },
    "settings.dwell_click": {
        "en": "Dwell Click",
        "id": "Klik Diam",
    },
    "settings.pinch_click": {
        "en": "Pinch Click",
        "id": "Klik Cubit",
    },
    "settings.mouth_click": {
        "en": "Mouth Click",
        "id": "Klik Mulut",
    },
    "settings.dwell_time": {
        "en": "Dwell Time (ms)",
        "id": "Waktu Diam (ms)",
    },
    "settings.dwell_radius": {
        "en": "Dwell Radius (px)",
        "id": "Radius Diam (px)",
    },
    "settings.camera_index": {
        "en": "Camera Index",
        "id": "Indeks Kamera",
    },
    "settings.target_fps": {
        "en": "Target FPS",
        "id": "Target FPS",
    },
    "settings.mirror_mode": {
        "en": "Mirror Mode",
        "id": "Mode Cermin",
    },
    "settings.auto_exposure": {
        "en": "Auto Exposure",
        "id": "Eksposur Otomatis",
    },
    "settings.auto_focus": {
        "en": "Auto Focus",
        "id": "Fokus Otomatis",
    },
    "settings.max_fps": {
        "en": "Max FPS",
        "id": "FPS Maksimum",
    },
    "settings.multi_threading": {
        "en": "Multi-Threading",
        "id": "Multi-Threading",
    },
    "settings.gpu_accel": {
        "en": "GPU Acceleration",
        "id": "Akselerasi GPU",
    },
    "settings.power_save": {
        "en": "Power Save Mode",
        "id": "Mode Hemat Daya",
    },
    "settings.show_preview": {
        "en": "Show Video Preview",
        "id": "Tampilkan Pratinjau Video",
    },
    "settings.show_overlay": {
        "en": "Show Overlay",
        "id": "Tampilkan Overlay",
    },
    "settings.cursor_trail": {
        "en": "Cursor Trail",
        "id": "Jejak Kursor",
    },
    "settings.audio_feedback": {
        "en": "Audio Feedback",
        "id": "Umpan Balik Audio",
    },
    "settings.click_sound": {
        "en": "Click Sound",
        "id": "Suara Klik",
    },
    "settings.high_contrast": {
        "en": "High Contrast",
        "id": "Kontras Tinggi",
    },
    "settings.large_ui": {
        "en": "Large UI",
        "id": "UI Besar",
    },
    "settings.notifications": {
        "en": "Show Notifications",
        "id": "Tampilkan Notifikasi",
    },

    # ── Onboarding ────────────────────────────────────────────────────────
    "onboard.welcome": {
        "en": "Welcome to KURSORIN",
        "id": "Selamat Datang di KURSORIN",
    },
    "onboard.welcome_desc": {
        "en": "Control your computer hands-free using\nhead movements, hand gestures, and eye tracking.\n\nThis quick setup will configure your environment\nand calibrate eye tracking for best accuracy.",
        "id": "Kontrol komputer Anda tanpa sentuhan\nmenggunakan gerakan kepala, gestur tangan, dan pelacakan mata.\n\nPengaturan cepat ini akan mengkonfigurasi lingkungan Anda\ndan mengkalibrasi pelacakan mata untuk akurasi terbaik.",
    },
    "onboard.get_started": {
        "en": "Get Started →",
        "id": "Mulai →",
    },
    "onboard.env_check": {
        "en": "Environment Check",
        "id": "Pemeriksaan Lingkungan",
    },
    "onboard.env_tips": {
        "en": "For the best experience, please ensure:\n\n  •  You are in a well-lit room\n  •  Your webcam can see your face and hands clearly\n  •  There is minimal background clutter",
        "id": "Untuk pengalaman terbaik, pastikan:\n\n  •  Anda berada di ruangan dengan pencahayaan baik\n  •  Webcam dapat melihat wajah dan tangan Anda dengan jelas\n  •  Latar belakang tidak terlalu ramai",
    },
    "onboard.eye_calib": {
        "en": "Eye Calibration",
        "id": "Kalibrasi Mata",
    },
    "onboard.calib_desc": {
        "en": "Calibrating your eye tracking improves accuracy.\n\nWhen calibration starts, dots will appear on screen.\nLook at each dot steadily until it moves.\nKeep your head relatively still during this process.",
        "id": "Kalibrasi pelacakan mata meningkatkan akurasi.\n\nSaat kalibrasi dimulai, titik akan muncul di layar.\nLihat setiap titik dengan stabil sampai berpindah.\nJaga kepala Anda tetap diam selama proses ini.",
    },
    "onboard.start_calibration": {
        "en": "Start Calibration",
        "id": "Mulai Kalibrasi",
    },
    "onboard.skip": {
        "en": "Skip",
        "id": "Lewati",
    },
    "onboard.back": {
        "en": "← Back",
        "id": "← Kembali",
    },
    "onboard.next": {
        "en": "Next →",
        "id": "Lanjut →",
    },
    "onboard.step_welcome": {
        "en": "Welcome",
        "id": "Selamat Datang",
    },
    "onboard.step_env": {
        "en": "Environment",
        "id": "Lingkungan",
    },
    "onboard.step_calib": {
        "en": "Calibration",
        "id": "Kalibrasi",
    },

    # ── Calibration window ────────────────────────────────────────────────
    "calib.title": {
        "en": "Eye Calibration",
        "id": "Kalibrasi Mata",
    },
    "calib.instruction": {
        "en": "Click each dot to calibrate  •  Press ESC to cancel",
        "id": "Klik setiap titik untuk kalibrasi  •  Tekan ESC untuk membatalkan",
    },
    "calib.complete": {
        "en": "Calibration Complete",
        "id": "Kalibrasi Selesai",
    },
    "calib.closing": {
        "en": "Closing in 2 seconds...",
        "id": "Menutup dalam 2 detik...",
    },

    # ── Lang command ──────────────────────────────────────────────────────
    "lang.current": {
        "en": "Current language: English",
        "id": "Bahasa saat ini: Bahasa Indonesia",
    },
    "lang.switched": {
        "en": "Language switched to",
        "id": "Bahasa diubah ke",
    },
    "lang.english": {
        "en": "English",
        "id": "English",
    },
    "lang.indonesian": {
        "en": "Bahasa Indonesia",
        "id": "Bahasa Indonesia",
    },

    # ── Info command ──────────────────────────────────────────────────────
    "info.title": {
        "en": "System Information",
        "id": "Informasi Sistem",
    },
    "info.help_desc": {
        "en": "Show detailed system and tracking info.",
        "id": "Tampilkan info sistem dan pelacakan secara detail.",
    },

    # ── Metrics ───────────────────────────────────────────────────────────
    "metric.fps": {
        "en": "FPS",
        "id": "FPS",
    },
    "metric.latency": {
        "en": "Latency",
        "id": "Latensi",
    },
    "metric.state": {
        "en": "State",
        "id": "Status",
    },
    "metric.frames": {
        "en": "Frames",
        "id": "Frame",
    },
    "metric.uptime": {
        "en": "Uptime",
        "id": "Waktu Aktif",
    },

    # ── Module labels ─────────────────────────────────────────────────────
    "module.tracking": {
        "en": "Tracking",
        "id": "Pelacakan",
    },
    "module.click": {
        "en": "Click",
        "id": "Klik",
    },
    "module.camera": {
        "en": "Camera",
        "id": "Kamera",
    },
    "module.performance": {
        "en": "Performance",
        "id": "Kinerja",
    },
    "module.setting": {
        "en": "Setting",
        "id": "Pengaturan",
    },
    "module.value": {
        "en": "Value",
        "id": "Nilai",
    },
    "module.module": {
        "en": "Module",
        "id": "Modul",
    },
    "module.methods": {
        "en": "Methods",
        "id": "Metode",
    },
    "module.resolution_fps": {
        "en": "Resolution / FPS",
        "id": "Resolusi / FPS",
    },
    "module.threading_gpu": {
        "en": "Threading / GPU",
        "id": "Threading / GPU",
    },

    # ── Updates ───────────────────────────────────────────────────────────
    "update.checking": {
        "en": "Checking for updates...",
        "id": "Memeriksa pembaruan...",
    },
    "update.available": {
        "en": "Update available! Run [bold]kursorin update[/bold] to apply.",
        "id": "Pembaruan tersedia! Jalankan [bold]kursorin update[/bold] untuk memasang.",
    },
    "update.up_to_date": {
        "en": "System is up to date.",
        "id": "Sistem sudah versi terbaru.",
    },
    "update.success": {
        "en": "Update successful! Please restart KURSORIN.",
        "id": "Pembaruan berhasil! Silakan mulai ulang KURSORIN.",
    },
    "update.pulling": {
        "en": "Pulling latest changes...",
        "id": "Mengunduh perubahan terbaru...",
    },
    "update.error_git": {
        "en": "Git not found. Please install Git to use automatic updates.",
        "id": "Git tidak ditemukan. Silakan pasang Git untuk pembaruan otomatis.",
    },
    "update.error_repo": {
        "en": "Not a Git repository. To enable automatic updates, please clone via 'git clone'.",
        "id": "Bukan repositori Git. Untuk mengaktifkan pembaruan otomatis, silakan klon via 'git clone'.",
    },
    "update.error_local": {
        "en": "Local changes detected. Use [bold]--force[/bold] to overwrite.",
        "id": "Terdeteksi perubahan lokal. Gunakan [bold]--force[/bold] untuk menimpa.",
    },
}


# ─── Language State ───────────────────────────────────────────────────────────

_current_lang: str = "en"


def get_lang() -> str:
    """Get the current language code."""
    return _current_lang


def set_lang(lang: str):
    """Set the current language ('en' or 'id')."""
    global _current_lang
    if lang in ("en", "id"):
        _current_lang = lang


def detect_lang() -> str:
    """Auto-detect language from config or system locale."""
    # Try config file
    try:
        cfg_path = Path.home() / ".kursorin" / "config.yaml"
        if cfg_path.exists():
            import yaml
            with open(cfg_path, "r") as f:
                data = yaml.safe_load(f) or {}
            lang = data.get("language", "").lower()
            if lang in ("id", "en"):
                return lang
    except Exception:
        pass

    # Try environment variable
    env_lang = os.environ.get("KURSORIN_LANG", "").lower()
    if env_lang in ("id", "en"):
        return env_lang

    # Try system locale
    try:
        sys_locale = locale.getdefaultlocale()[0] or ""
        if sys_locale.startswith("id"):
            return "id"
    except Exception:
        pass

    return "en"


def init_lang():
    """Initialize language from auto-detection."""
    set_lang(detect_lang())


def save_lang(lang: str):
    """Save language preference to config file."""
    try:
        import yaml
        cfg_path = Path.home() / ".kursorin" / "config.yaml"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        if cfg_path.exists():
            with open(cfg_path, "r") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    data = loaded

        data["language"] = lang

        with open(cfg_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except Exception:
        pass


# ─── Translation Function ────────────────────────────────────────────────────

def t(key: str, **kwargs) -> str:
    """
    Translate a string key to the current language.

    Usage:
        t("cli.description")
        t("doctor.passed_n", passed=5, total=7)
    """
    entry = _STRINGS.get(key)
    if entry is None:
        return key  # Fallback: return the key itself

    text = entry.get(_current_lang, entry.get("en", key))

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass

    return text
