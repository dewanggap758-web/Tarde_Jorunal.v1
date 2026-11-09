# Hosting di PythonAnywhere Beginner

Panduan ini memakai SQLite khusus untuk website di PythonAnywhere. Database
Supabase lokal tetap digunakan selama `DJANGO_DATABASE` tidak diubah. Data
SQLite di hosting terpisah dari Supabase dan tidak otomatis tersinkron.

## 1. Buat website gratis

1. Buat akun [PythonAnywhere Beginner](https://www.pythonanywhere.com/registration/register/beginner/).
2. Dari tab **Web**, buat web app pada domain gratis akun Anda.
3. Pilih **Manual configuration** dan Python **3.13**.

## 2. Unduh aplikasi dan pasang dependency

Buka **Consoles → Bash** dan jalankan:

```bash
git clone https://github.com/dewanggap758-web/Tarde_Jorunal.v1.git
cd ~/Tarde_Jorunal.v1
mkvirtualenv --python=python3.13 trade-journal
pip install -r requirements.txt
```

Jika `mkvirtualenv` tidak tersedia, ikuti petunjuk virtualenv di dokumentasi
PythonAnywhere. Gunakan Python yang sama dengan pilihan web app.

## 3. Atur WSGI dan environment

Pada tab **Web**, buka tautan file WSGI. Ganti `<username>` dengan username
PythonAnywhere Anda, lalu sesuaikan blok Django agar seperti berikut. Buat
secret key baru di Bash dengan
`python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
dan masukkan hasilnya hanya ke file WSGI privat Anda—jangan ke GitHub atau chat.

```python
import os
import sys

project_path = '/home/<username>/Tarde_Jorunal.v1'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'backend_core.settings'
os.environ['DJANGO_DEBUG'] = 'false'
os.environ['DJANGO_SECRET_KEY'] = 'PASTE_SECRET_KEY_BARU_DI_SINI'
os.environ['DJANGO_DATABASE'] = 'sqlite'
os.environ['SQLITE_DATABASE_PATH'] = '/home/<username>/trade-journal-data/db.sqlite3'
os.environ['DJANGO_ALLOWED_HOSTS'] = '<username>.pythonanywhere.com'
os.environ['DJANGO_SECURE_SSL_REDIRECT'] = 'false'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Di bagian **Virtualenv** tab Web, masukkan:
`/home/<username>/.virtualenvs/trade-journal`.

## 4. Buat database dan kumpulkan static files

Kembali ke Bash console. Jalankan perintah berikut di folder proyek. Saat
diminta, tempel secret key yang sama dengan yang disimpan di file WSGI; input
tidak akan ditampilkan. Ganti `<username>` dengan username PythonAnywhere Anda.

```bash
mkdir -p ~/trade-journal-data
read -s -p "Secret key WSGI: " DJANGO_SECRET_KEY
echo
export DJANGO_SECRET_KEY
export DJANGO_DEBUG=false
export DJANGO_DATABASE=sqlite
export SQLITE_DATABASE_PATH="$HOME/trade-journal-data/db.sqlite3"
export DJANGO_ALLOWED_HOSTS='<username>.pythonanywhere.com'
export DJANGO_SECURE_SSL_REDIRECT=false
python manage.py migrate
python manage.py collectstatic --no-input
```

Database disimpan di luar folder Git, jadi memperbarui kode tidak menghapus data.

## 5. Aktifkan HTTPS dan arahkan static files

Di bagian **Static files** pada tab Web, tambahkan:

- URL: `/static/`
- Directory: `/home/<username>/Tarde_Jorunal.v1/staticfiles`

Di bagian **Security** tab Web, aktifkan **Force HTTPS**. Pengaturan ini
memaksa koneksi memakai HTTPS; karena itu `DJANGO_SECURE_SSL_REDIRECT` pada
WSGI disetel `false` agar tidak terjadi redirect loop di belakang proxy.
Klik **Reload** pada tab Web, lalu buka URL HTTPS akun PythonAnywhere Anda.

## Database dan backup

Migrasi membuat tabel SQLite secara otomatis. File database berada di
`~/trade-journal-data/db.sqlite3` pada akun hosting. Backup file ini berkala
dari Bash, misalnya:

```bash
cp ~/trade-journal-data/db.sqlite3 ~/trade-journal-backup.sqlite3
```

Trade yang dicatat di website ini tersimpan di SQLite dan tidak muncul di
Supabase lokal. Akun gratis PythonAnywhere membatasi koneksi keluar; SQLite
menghindari koneksi PostgreSQL keluar tersebut.

Panduan resmi:

- [Deploy Django project yang sudah ada](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/)
- [Konfigurasi static files](https://help.pythonanywhere.com/pages/DjangoStaticFiles/)
- [Virtualenvs](https://help.pythonanywhere.com/pages/VirtualenvsExplained/)
