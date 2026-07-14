# 🎮 PS Rental Cloud Vault

Aplikasi web manajemen rental PlayStation 3 yang **memanfaatkan S3 sebagai
modul manajemen cloud storage penuh** ("Cloud Vault") — bukan sekadar upload
sekali pakai, melainkan sistem file management lengkap (upload, download,
delete, rename, buat folder, preview gambar) yang terorganisir otomatis per
transaksi sewa.

Dibangun dengan **Flask (Python)**, **boto3**, dan **SQLite**. Untuk
penyimpanan S3, proyek ini memakai **LocalStack** (emulator AWS S3 lokal via
Docker) sebagai default — tidak butuh akun AWS asli — namun bisa diarahkan ke
AWS S3 sungguhan kapan saja tanpa mengubah kode. Mendukung 3 cara menjalankan:
**langsung dengan Python**, **penuh lewat Docker Compose** (app + LocalStack
sekaligus), dan siap di-push ke **Repository GitHub**.

## ✨ Fitur

### Manajemen Bisnis Rental
| Fitur | Keterangan |
|---|---|
| Dashboard | Statistik unit, penyewaan aktif, pelanggan, pendapatan, & storage vault |
| Manajemen Unit PS3 | Tambah unit, ubah status (Tersedia/Disewa/Maintenance), hapus |
| Manajemen Pelanggan | Data pelanggan (nama, telepon, email, alamat) |
| Transaksi Sewa | Buat transaksi baru, hitung otomatis total biaya berdasarkan durasi, tandai dikembalikan |

### Cloud Vault — Modul Manajemen S3 (inti tugas Cloud Computing)
| Fitur | Keterangan |
|---|---|
| Folder Otomatis per Transaksi | Setiap transaksi baru otomatis dibuatkan folder S3: `rentals/{id}-{kode_unit}/` |
| Browse File/Folder | Navigasi folder virtual S3 dengan breadcrumb |
| Upload | Drag & drop / pilih file, multi-file sekaligus (foto kondisi unit, bukti bayar) |
| Download | Lewat presigned URL (aman, tanpa membuat objek public) |
| Delete | File tunggal maupun folder beserta isinya (rekursif) |
| Rename | File maupun folder (implementasi copy + delete di S3) |
| Create Folder | Folder virtual tambahan (misal per kategori dokumen) |
| Preview Gambar | Modal preview langsung di browser via presigned URL |

## 🗂 Struktur Proyek

```
ps-rental-cloud-vault/
├── app.py                 # Entry point Flask
├── config.py               # Konfigurasi & env
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── static/css/style.css    # Tema "Neon Console"
├── static/js/app.js
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── units.html
│   ├── customers.html
│   ├── rentals.html
│   ├── rental_form.html
│   ├── rental_detail.html
│   └── vault.html          # UI file manager S3
├── routes/
│   ├── dashboard.py
│   ├── units.py
│   ├── customers.py
│   ├── rentals.py
│   └── vault.py             # Semua endpoint manajemen S3
├── services/
│   ├── s3_service.py        # Semua logic boto3 terpusat
│   └── db_service.py        # Query database rental
├── database/
│   └── models.py            # Skema SQLite + seed data
├── utils/
│   └── helper.py
└── docs/
    └── Manual.pdf
```

## ⚙️ Penyimpanan: LocalStack (bukan AWS S3 asli)

Aplikasi ini secara default dikonfigurasi memakai **LocalStack** — emulator
AWS S3 yang jalan 100% di komputer/laptop sendiri lewat Docker. Artinya:

- **Tidak perlu akun AWS**, tidak perlu kartu kredit, tidak ada biaya.
- Semua endpoint S3 (list, upload, delete, rename, presigned URL) tetap
  memakai **boto3 asli** — cara pemakaian di kode sama persis seperti ke AWS
  S3 sungguhan, hanya `endpoint_url`-nya diarahkan ke LocalStack.
- Kalau suatu saat ingin pindah ke AWS S3 asli (misalnya untuk deployment
  produksi), tinggal ganti isi `.env` — tidak perlu ubah kode sama sekali
  (lihat bagian "Pindah ke AWS S3 Asli" di bawah).

### Instalasi LocalStack

LocalStack dijalankan sebagai container Docker. Ada 2 cara pakai:

**Cara A — LocalStack via Docker CLI langsung (untuk `python app.py` biasa):**
```bash
docker run -d --name localstack -p 4566:4566 -e SERVICES=s3 localstack/localstack:3
```

**Cara B — LocalStack otomatis ikut naik lewat `docker compose up`**
(lihat bagian Docker di bawah, tidak perlu perintah tambahan).

### Membuat Bucket di LocalStack

Setelah LocalStack jalan, buat bucket vault (sekali saja). Aplikasi
sebenarnya sudah otomatis mencoba membuat bucket ini saat start
(`ensure_bucket_exists()`), tapi bisa juga dibuat manual:

```bash
# Opsi 1: pakai AWS CLI biasa, arahkan endpoint ke LocalStack
aws --endpoint-url=http://localhost:4566 s3 mb s3://ps-rental-cloud-vault

# Opsi 2: pakai awslocal (wrapper AWS CLI khusus LocalStack, jika terinstal)
awslocal s3 mb s3://ps-rental-cloud-vault

# Cek isi bucket
aws --endpoint-url=http://localhost:4566 s3 ls s3://ps-rental-cloud-vault --recursive
```

## 🚀 Menjalankan Secara Lokal (Python, tanpa Docker untuk app)

```bash
git clone https://github.com/username-anda/ps-rental-cloud-vault.git
cd ps-rental-cloud-vault

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 1) Jalankan LocalStack (lihat Cara A di atas) jika belum jalan
docker run -d --name localstack -p 4566:4566 -e SERVICES=s3 localstack/localstack:3

# 2) Siapkan .env
cp .env.example .env
# .env.example SUDAH default ke LocalStack (AWS_ENDPOINT_URL=http://localhost:4566)
# tidak perlu ubah apa-apa untuk mulai mencoba

# 3) Jalankan aplikasi
python app.py
```

Buka **http://localhost:5000**. Database SQLite (`rental.db`) otomatis
dibuat dengan 3 unit contoh saat pertama kali dijalankan, dan bucket vault
otomatis dibuat di LocalStack.

## 🐳 Menjalankan Semuanya Lewat Docker (app + LocalStack sekaligus)

`docker-compose.yml` sudah berisi **dua service**: `localstack` (emulator S3)
dan `app` (aplikasi Flask), sudah saling terhubung dalam satu network.

```bash
cp .env.example .env   # default sudah cocok untuk mode Docker+LocalStack
touch rental.db
docker compose up --build
```

Tunggu sampai LocalStack sehat (`healthcheck`) baru container `app` ikut
jalan otomatis. Buka **http://localhost:5000**.

> **Kenapa ada 2 variabel endpoint di `docker-compose.yml`?**
> Di dalam jaringan Docker, container `app` memanggil LocalStack lewat nama
> service (`http://localstack:4566`). Tapi saat aplikasi membuat **presigned
> URL** untuk didownload/preview lewat **browser** di komputer host, host
> `localstack` itu tidak bisa diakses dari luar container — makanya perlu
> `AWS_ENDPOINT_URL_PUBLIC=http://localhost:4566` supaya presigned URL yang
> dikirim ke browser memakai host yang benar. Ini sudah diatur otomatis di
> `docker-compose.yml`, tidak perlu diutak-atik.

### Menghentikan & membersihkan
```bash
docker compose down          # hentikan container
docker compose down -v       # + hapus volume data LocalStack (reset total)
```

## 🔁 Pindah ke AWS S3 Asli (opsional, untuk production)

Kode sama sekali tidak berubah — cukup ganti isi `.env`:

1. Buat IAM User di AWS Console → beri permission `AmazonS3FullAccess`
   (atau policy custom least-privilege di bawah).
2. Generate **Access Key ID** dan **Secret Access Key**.
3. Di `.env`, isi kredensial asli, lalu **kosongkan**
   `AWS_ENDPOINT_URL` dan `AWS_ENDPOINT_URL_PUBLIC` (hapus nilainya, biarkan
   kosong) — begitu kosong, boto3 otomatis kembali ke AWS S3 sungguhan.
4. Pastikan `VAULT_BUCKET` unik secara global.

Contoh IAM Policy minimal (least privilege):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:CreateBucket",
        "s3:HeadBucket"
      ],
      "Resource": "*"
    }
  ]
}
```

## 📤 Upload Kode ke GitHub

```bash
git init
git add .
git commit -m "Initial commit - PS Rental Cloud Vault"
git branch -M main
git remote add origin https://github.com/username-anda/ps-rental-cloud-vault.git
git push -u origin main
```

File `.env` dan `rental.db` sudah dikecualikan lewat `.gitignore` sehingga
tidak ikut ter-commit. Karena kredensial default di `.env.example` untuk
LocalStack hanya `test`/`test` (bukan kredensial asli), repository ini aman
dipublikasikan sebagai repo publik di GitHub tanpa risiko kebocoran
kredensial.

## 📄 Manual Penggunaan

Lihat `docs/Manual.pdf` untuk panduan lengkap bergambar-alur mengenai cara
memakai setiap fitur, mulai dari mendaftarkan unit, membuat transaksi, hingga
mengelola file di Cloud Vault.

## 🔒 Catatan Keamanan

- Kredensial AWS **tidak pernah** di-hardcode — selalu lewat `.env` (sudah
  masuk `.gitignore`).
- Download & preview gambar menggunakan **presigned URL** yang kedaluwarsa
  otomatis, bukan membuat objek menjadi public.
- Untuk AWS S3 asli: gunakan IAM User dengan permission terbatas, jangan
  pakai root credentials.
- Kredensial LocalStack (`test`/`test`) hanya berlaku secara lokal dan tidak
  terhubung ke AWS sungguhan — aman untuk dipakai di repository publik
  sebagai contoh default di `.env.example`.

## 🧑‍💻 Teknologi

- **Backend:** Python, Flask, boto3, SQLite (sqlite3)
- **Frontend:** HTML5, CSS3 custom ("Neon Console" theme), vanilla JavaScript
- **Storage:** AWS S3-compatible — LocalStack untuk pengembangan lokal, bisa
  diarahkan ke AWS S3 asli untuk produksi tanpa mengubah kode
- **Deployment:** Docker Compose (app + LocalStack) & Gunicorn

---
Dibuat sebagai tugas mata kuliah Cloud Computing — Universitas Islam Sultan
Agung (UNISSULA). Konsep: sistem rental PS3 dengan modul manajemen S3
(via LocalStack) sebagai media penyimpanan dokumentasi transaksi (Cloud Vault).
