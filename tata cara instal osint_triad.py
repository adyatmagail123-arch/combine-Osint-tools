Step by step cara membuat nya silahkan buat sendiri.
pastikan sudah menginstal tools : Maigret, Holehe, theHarvester.
langkah pertama : buat folder pada direktori yang di pilih dengan nama osint_triad
langkah kedua : lalu masuk ke dalam folder yang di buat tadi dan membuat file menggunakan "nano osint_triad"
langkah ketiga : copas semua kode yang berada di bawah ini.
----------------------------------------------------------------------------------------------------------------------------------------
#!/usr/bin/env python3
import os
import sys
import subprocess
import json
import re
import requests
from urllib.parse import quote_plus
from datetime import datetime

# --- PATH TOOLS CUSTOM ---
MAIGRET_PATH = "/home/hacking/.local/share/pipx/venvs/maigret/bin/maigret"
HOLEHE_PATH = "/home/hacking/.local/share/pipx/venvs/holehe/bin/holehe"
THEHARVESTER_PATH = "/usr/bin/theharvester"

def run_command(cmd, timeout=90):
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=dict(os.environ, PYTHONUNBUFFERED="1")
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "[ERROR] Command timed out"
    except Exception as e:
        return f"[ERROR] {str(e)}"

def search_google(query):
    try:
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        titles = re.findall(r'<h3 class=".*?">([^<]+)</h3>', resp.text)
        return titles[:5]
    except:
        return []

def extract_domain(email):
    return email.split("@")[1] if "@" in email else None

# === FUNGSI HTML REPORT (DI LUAR main()) ===
def generate_html_report(report_data, filename="osint_report.html"):
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Laporan OSINT Triad</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f9f9f9; }}
        .container {{ max-width: 900px; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #d32f2f; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        h2 {{ color: #333; margin-top: 25px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 6px; }}
        .section {{ margin-bottom: 20px; }}
        .input-box {{ background: #f1f8e9; padding: 12px; border-left: 4px solid #7cb342; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Laporan OSINT Triad</h1>
        <div class="input-box">
            <strong>Input Investigasi:</strong><br>
            Email: {report_data['input']['email']}<br>
            Username: {report_data['input']['username']}<br>
            Telepon: {report_data['input']['phone']}
        </div>

        <div class="section">
            <h2>📊 Temuan</h2>
            <ul>
                <li><strong>Akun Sosial:</strong> {report_data['findings'].get('social_accounts', 'Tidak tersedia')}</li>
                <li><strong>Email Terdaftar di Layanan:</strong> {report_data['findings'].get('email_registered', 'Tidak diketahui')}</li>
                <li><strong>Jejak Nomor Telepon:</strong>
                    {'<br>&nbsp;&nbsp;' + '<br>&nbsp;&nbsp;• '.join(report_data['findings'].get('phone_mentions', [])) if report_data['findings'].get('phone_mentions') else 'Tidak ditemukan'}
                </li>
                <li><strong>Email Terkait (Domain):</strong>
                    {'<br>&nbsp;&nbsp;' + '<br>&nbsp;&nbsp;• '.join(report_data['findings'].get('related_emails', [])) if report_data['findings'].get('related_emails') else 'Tidak ada'}
                </li>
            </ul>
        </div>

        <p><em>Dibuat pada {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Hanya berisi data publik</em></p>
    </div>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

def main():
    if len(sys.argv) != 4:
        print("Penggunaan: python3 osint_triad_custom.py <email> <username> <phone>")
        print("Contoh: python3 osint_triad_custom.py target@instansi.go.id joko_pns +6281234567890")
        sys.exit(1)

    email = sys.argv[1].strip()
    username = sys.argv[2].strip()
    phone = sys.argv[3].strip()

    print("="*60)
    print("🔍 OSINT TRIAD ANALYZER v1.1 (Custom Path)")
    print("   Menggunakan path tools spesifik pengguna")
    print("="*60 + "\n")

    report = {
        "input": {"email": email, "username": username, "phone": phone},
        "findings": {}
    }

    # === 1. Maigret ===
    print("[*] Menjalankan Maigret...")
    maigret_cmd = f"{MAIGRET_PATH} {username} --timeout 15 --no-color --print-not-found"
    maigret_out = run_command(maigret_cmd)

    if "No accounts found" not in maigret_out and "[ERROR]" not in maigret_out:
        report["findings"]["social_accounts"] = "Ditemukan akun aktif"
        print("\n✅ MAIGRET RESULT:")
        print(maigret_out)
    else:
        report["findings"]["social_accounts"] = "Tidak ditemukan"
        print("[ ] Tidak ada akun sosial ditemukan.")

    # === 2. Holehe ===
    print("\n[*] Menjalankan Holehe...")
    holehe_cmd = f"{HOLEHE_PATH} {email} --only-used"
    holehe_out = run_command(holehe_cmd)

    if "[+]" in holehe_out:
        report["findings"]["email_registered"] = "Email terdaftar di layanan publik"
        print("\n✅ HOLEHE RESULT:")
        for line in holehe_out.split('\n'):
            if '[+]' in line:
                print(line)
    else:
        report["findings"]["email_registered"] = "Tidak terdaftar"
        print("[ ] Email tidak ditemukan di database Holehe.")

    # === 3. Reverse Phone Lookup via Google ===
    print("\n[*] Melakukan reverse lookup nomor telepon...")
    google_results = search_google(phone)

    if google_results:
        report["findings"]["phone_mentions"] = google_results[:3]
        print("\n✅ GOOGLE PHONE MENTIONS:")
        for res in google_results[:3]:
            print(f"  • {res}")
    else:
        report["findings"]["phone_mentions"] = []
        print("[ ] Tidak ada jejak publik untuk nomor tersebut.")

    # === 4. TheHarvester (jika domain institusi) ===
    domain = extract_domain(email)
    if domain and domain not in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]:
        print(f"\n[*] Menjalankan theHarvester pada domain: {domain}")
        harv_cmd = f"{THEHARVESTER_PATH} -d {domain} -b all -l 200"
        harv_out = run_command(harv_cmd)

        emails_found = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', harv_out)
        unique_emails = list(set(e for e in emails_found if domain in e))

        if len(unique_emails) > 1:
            report["findings"]["related_emails"] = unique_emails[:10]
            print(f"\n✅ DITEMUKAN {len(unique_emails)} EMAIL TERKAIT:")
            for e in unique_emails[:10]:
                print(f"  • {e}")
        else:
            report["findings"]["related_emails"] = []
            print("[ ] Tidak ada email internal tambahan ditemukan.")

    # === Simpan Laporan ===
    with open("osint_report.json", "w") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    # Simpan HTML
    generate_html_report(report, "osint_report.html")

    print("\n" + "="*60)
    print("📄 Laporan disimpan sebagai:")
    print("   • osint_report.json")
    print("   • osint_report.html")
    print("💡 Gunakan hanya untuk investigasi legal & data publik.")
    print("="*60)

if __name__ == "__main__":
    main()

----------------------------------------------------------------------------------------------------------------------------------------
langkah ke empat : setelah copas isi code di dalam file "osint_triad.py", di save dan lakukan verifikasi dengan ara "chmod osint_triad.py"
langkah ke lima : setelah sudah di chmod, maka script sudah bisa di jalankan
langkah ke enam : silahkan jalan menggunakan perintah "python3 osint_triad.py target@gmil.com usernametarget nomortelpontarget
catatan penting : pastikan anda sudah menginstal 3 tools yang sudah saya sebutkan, dan untuk memasukkan code perhatikan path tools yang anda instal berada lalu sesuaikan di code, agar tools dapat di panggil.

untuk mengganti path cari code berisi sebagai berikut:
# --- PATH TOOLS CUSTOM ---
MAIGRET_PATH = "/home/hacking/.local/share/pipx/venvs/maigret/bin/maigret"
HOLEHE_PATH = "/home/hacking/.local/share/pipx/venvs/holehe/bin/holehe"
THEHARVESTER_PATH = "/usr/bin/theharvester"

happy osint guys.......
