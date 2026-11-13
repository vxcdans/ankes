# AntiGCastBot

Bot moderasi grup Telegram berbasis Python + python-telegram-bot + SQLite.

## Fitur
- Anti-flood / burst message
- Deteksi forward beruntun
- Deteksi pesan teks berulang
- Anti-link spam (3 atau lebih URL dalam satu pesan)
- Anti-mention massal (5 atau lebih mention)
- Warning otomatis dan mute setelah batas warning
- Whitelist anggota
- Perintah konfigurasi admin
- Database SQLite lokal

> Bot ini ditujukan untuk moderasi grup yang dikelola atau atas izin admin. Bot tidak melakukan broadcast massal, tidak mengambil konten dari grup/channel lain, dan tidak melewati proteksi Telegram.

## 1. Buat bot
1. Buka Telegram dan chat `@BotFather`.
2. Jalankan `/newbot`, ikuti instruksi, lalu simpan token.
3. Matikan Privacy Mode lewat `/setprivacy` jika ingin bot memeriksa semua pesan grup.
4. Tambahkan bot ke grup dan jadikan admin. Berikan izin **Delete Messages** dan **Restrict Members**.

## 2. Instalasi Ubuntu 22.04/24.04
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
git clone https://github.com/USERNAME/AntiGCastBot.git
cd AntiGCastBot
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
nano .env
```
Isi `BOT_TOKEN` pada `.env`, lalu simpan. Lindungi file:
```bash
chmod 600 .env
```

## 3. Jalankan
```bash
source .venv/bin/activate
python main.py
```
Hentikan dengan `Ctrl+C`.

## 4. Menjalankan sebagai systemd service
Ganti `YOUR_LINUX_USER` dan `/home/YOUR_LINUX_USER/AntiGCastBot` sesuai lokasi proyek.
```bash
sudo nano /etc/systemd/system/antigcastbot.service
```
Isi:
```ini
[Unit]
Description=AntiGCastBot Telegram Moderation Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=YOUR_LINUX_USER
WorkingDirectory=/home/YOUR_LINUX_USER/AntiGCastBot
EnvironmentFile=/home/YOUR_LINUX_USER/AntiGCastBot/.env
ExecStart=/home/YOUR_LINUX_USER/AntiGCastBot/.venv/bin/python /home/YOUR_LINUX_USER/AntiGCastBot/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
Aktifkan:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now antigcastbot
sudo systemctl status antigcastbot
journalctl -u antigcastbot -f
```

## Perintah
- `/start`
- `/help`
- `/status`
- `/settings`
- `/antigcast on` atau `/antigcast off`
- `/antispam on` atau `/antispam off`
- `/setlimit 6` (rentang 3-30)
- Reply pesan anggota lalu `/whitelist`
- Reply pesan anggota lalu `/unwhitelist`
- Reply pesan anggota lalu `/warn`

## Catatan operasional
- Perintah pengaturan hanya bisa dijalankan admin grup.
- Bot harus menjadi admin agar dapat menghapus pesan dan membatasi anggota.
- Nonaktifkan Privacy Mode di BotFather agar bot menerima pesan biasa.
- Deteksi burst berjalan di memori proses; warning dan pengaturan disimpan di SQLite.
- Untuk menghindari false positive, uji dulu di grup kecil dan sesuaikan limit.
- Simpan `.env` dengan aman dan jangan commit token ke GitHub.
