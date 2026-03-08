#!/usr/bin/env python3
"""
collect_code.py
---------------
Verilen bir klasördeki tüm .py ve .dart dosyalarını bulur,
yapay zekanın kolayca anlayabileceği formatta tek bir .txt dosyasına toplar.
Paket/bağımlılık klasörlerini otomatik olarak atlar.

Kullanım:
    python collect_code.py <kaynak_klasor> [cikti_dosyasi] [seçenekler]

Örnekler:
    python collect_code.py ./projem
    python collect_code.py ./projem cikti.txt
    python collect_code.py C:/HEAI
    python collect_code.py ./projem --exclude logs --exclude data
"""

import os
import sys
import argparse
from datetime import datetime

# ─── Ayarlar ────────────────────────────────────────────────────────────────
HEDEF_UZANTILAR = {".py", ".dart"}
SEPARATOR_KALIN = "=" * 80
SEPARATOR_INCE  = "-" * 80

# Otomatik atlanan klasör isimleri (büyük/küçük harf duyarsız)
ATLANAN_KLASORLER = {
    # Python sanal ortamlar
    "venv", "env", ".venv", ".env", "virtualenv", ".virtualenv",
    "venv32", "venv64", ".tox", "pyenv",
    # Python paketler
    "site-packages", "dist-packages", "lib2to3",
    # Build / dağıtım
    "__pycache__", "build", "dist", "*.egg-info", ".eggs",
    # Dart / Flutter
    ".dart_tool", ".pub-cache", ".pub", "build",
    # Node / JS
    "node_modules",
    # IDE / araçlar
    ".idea", ".vscode", ".gradle", ".git", ".svn",
    # Diğer
    "migrations",  # Django migration dosyaları (genellikle otomatik üretilir)
}


def venv_mi(klasor_yolu: str) -> bool:
    """Klasörün Python sanal ortamı olup olmadığını tespit eder."""
    # pyvenv.cfg varsa kesinlikle venv'dir
    if os.path.isfile(os.path.join(klasor_yolu, "pyvenv.cfg")):
        return True
    # Windows venv yapısı: Scripts/python.exe + Lib/site-packages
    if (os.path.isdir(os.path.join(klasor_yolu, "Scripts")) and
            os.path.isdir(os.path.join(klasor_yolu, "Lib", "site-packages"))):
        return True
    # Linux/Mac venv yapısı: bin/python + lib/pythonX.X/site-packages
    if os.path.isdir(os.path.join(klasor_yolu, "bin")):
        bin_python = os.path.join(klasor_yolu, "bin", "python")
        bin_python3 = os.path.join(klasor_yolu, "bin", "python3")
        if os.path.exists(bin_python) or os.path.exists(bin_python3):
            return True
    return False


def gitignore_oku(klasor: str) -> set:
    """
    Klasördeki .gitignore dosyasını okur,
    atlanacak klasör isimlerini döndürür (basit eşleşme).
    """
    atlananlar = set()
    gitignore_yolu = os.path.join(klasor, ".gitignore")
    if not os.path.isfile(gitignore_yolu):
        return atlananlar
    try:
        with open(gitignore_yolu, "r", encoding="utf-8") as f:
            for satir in f:
                satir = satir.strip()
                if not satir or satir.startswith("#"):
                    continue
                # Klasör işaretlerini temizle: venv/ → venv
                temiz = satir.rstrip("/").lstrip("/").strip()
                if temiz and "/" not in temiz and "\\" not in temiz:
                    atlananlar.add(temiz.lower())
    except Exception:
        pass
    return atlananlar


def atlanacak_mi(klasor_adi: str, tam_yol: str, ekstra_atlanacaklar: set) -> bool:
    """Klasörün atlanıp atlanmayacağına karar verir."""
    ad_kucuk = klasor_adi.lower()

    # Gizli klasörler
    if klasor_adi.startswith("."):
        return True

    # Bilinen kötü klasörler
    if ad_kucuk in ATLANAN_KLASORLER:
        return True

    # Kullanıcının eklediği ekstra klasörler
    if ad_kucuk in ekstra_atlanacaklar:
        return True

    # .gitignore'dan gelen kurallar
    # (üst fonksiyonda zaten ekleniyor, burada tekrar kontrol)

    # venv tespiti (isimden bağımsız)
    if venv_mi(tam_yol):
        return True

    return False


def dosyalari_topla(kaynak_klasor: str, ekstra_atlanacaklar: set) -> list[dict]:
    """Klasörü özyinelemeli tarar, hedef dosyaları döndürür."""
    bulunan = []

    # Kök klasördeki .gitignore'u oku
    gitignore_atlananlar = gitignore_oku(kaynak_klasor)
    ekstra_atlanacaklar = ekstra_atlanacaklar | gitignore_atlananlar

    for kok, klasorler, dosyalar in os.walk(kaynak_klasor):
        # Alt klasörleri filtrele (os.walk'u yönlendirmek için in-place değiştir)
        klasorler[:] = [
            k for k in sorted(klasorler)
            if not atlanacak_mi(k, os.path.join(kok, k), ekstra_atlanacaklar)
        ]

        for dosya in sorted(dosyalar):
            _, uzanti = os.path.splitext(dosya)
            if uzanti.lower() in HEDEF_UZANTILAR:
                tam_yol = os.path.join(kok, dosya)
                goreceli_yol = os.path.relpath(tam_yol, kaynak_klasor)

                mtime = os.path.getmtime(tam_yol)
                son_degisim = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

                bulunan.append({
                    "tam_yol":      tam_yol,
                    "goreceli_yol": goreceli_yol,
                    "dosya_adi":    dosya,
                    "uzanti":       uzanti.lower(),
                    "dil":          "Python" if uzanti.lower() == ".py" else "Dart",
                    "son_degisim":  son_degisim,
                })

    # Önce dile, sonra yola göre sırala
    bulunan.sort(key=lambda x: (x["dil"], x["goreceli_yol"]))
    return bulunan


def dosya_oku(tam_yol: str) -> tuple[str, str | None]:
    """Dosyayı okur. (içerik, hata_mesajı) döndürür."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            with open(tam_yol, "r", encoding=encoding) as f:
                return f.read(), None
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return "", str(e)
    return "", "Dosya okunamadı: desteklenen encoding bulunamadı."


def cikti_yaz(dosyalar: list[dict], cikti_yolu: str, kaynak_klasor: str,
              atlanan_klasorler: set) -> dict:
    """Tüm dosyaları formatlı şekilde tek bir .txt'ye yazar."""
    istatistik = {
        "toplam_dosya":  len(dosyalar),
        "python_dosya":  sum(1 for d in dosyalar if d["dil"] == "Python"),
        "dart_dosya":    sum(1 for d in dosyalar if d["dil"] == "Dart"),
        "toplam_satir":  0,
        "hatali_dosya":  0,
    }

    with open(cikti_yolu, "w", encoding="utf-8") as cikti:

        # ── Başlık Bloğu ──────────────────────────────────────────────────
        cikti.write(SEPARATOR_KALIN + "\n")
        cikti.write("KOD TOPLAMA RAPORU\n")
        cikti.write(SEPARATOR_KALIN + "\n")
        cikti.write(f"Oluşturulma Tarihi : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        cikti.write(f"Kaynak Klasör      : {os.path.abspath(kaynak_klasor)}\n")
        cikti.write(f"Çıktı Dosyası      : {os.path.abspath(cikti_yolu)}\n")
        cikti.write(f"Toplam Dosya       : {istatistik['toplam_dosya']} "
                    f"(Python: {istatistik['python_dosya']}, "
                    f"Dart: {istatistik['dart_dosya']})\n")
        if atlanan_klasorler:
            ekstra_liste = ", ".join(sorted(atlanan_klasorler))
            cikti.write(f"Ekstra Atlananlar  : {ekstra_liste}\n")
        cikti.write(SEPARATOR_KALIN + "\n\n")

        # ── İçindekiler ───────────────────────────────────────────────────
        cikti.write("İÇİNDEKİLER\n")
        cikti.write(SEPARATOR_INCE + "\n")
        for i, d in enumerate(dosyalar, 1):
            cikti.write(
                f"  {i:>3}. [{d['dil']:<6}]  "
                f"{d['goreceli_yol']:<45}  "
                f"(son değişim: {d['son_degisim']})\n"
            )
        cikti.write("\n" + SEPARATOR_KALIN + "\n\n")

        # ── Dosya İçerikleri ──────────────────────────────────────────────
        for i, d in enumerate(dosyalar, 1):
            icerik, hata = dosya_oku(d["tam_yol"])

            satir_sayisi = (icerik.count("\n") +
                            (1 if icerik and not icerik.endswith("\n") else 0))
            istatistik["toplam_satir"] += satir_sayisi
            if hata:
                istatistik["hatali_dosya"] += 1

            cikti.write(SEPARATOR_KALIN + "\n")
            cikti.write(f"DOSYA #{i}\n")
            cikti.write(SEPARATOR_INCE + "\n")
            cikti.write(f"  Ad            : {d['dosya_adi']}\n")
            cikti.write(f"  Dil           : {d['dil']}\n")
            cikti.write(f"  Yol           : {d['goreceli_yol']}\n")
            cikti.write(f"  Son Değişim   : {d['son_degisim']}\n")
            cikti.write(f"  Satır         : {satir_sayisi}\n")
            if hata:
                cikti.write(f"  HATA          : {hata}\n")
            cikti.write(SEPARATOR_INCE + "\n\n")

            if hata:
                cikti.write(f"[HATA: Dosya okunamadı — {hata}]\n")
            else:
                cikti.write(icerik)
                if icerik and not icerik.endswith("\n"):
                    cikti.write("\n")

            cikti.write("\n" + SEPARATOR_KALIN + "\n")
            cikti.write(f"# DOSYA #{i} SONU: {d['goreceli_yol']}\n")
            cikti.write(SEPARATOR_KALIN + "\n\n")

        # ── Özet ──────────────────────────────────────────────────────────
        cikti.write(SEPARATOR_KALIN + "\n")
        cikti.write("ÖZET\n")
        cikti.write(SEPARATOR_INCE + "\n")
        cikti.write(f"  Toplam Dosya  : {istatistik['toplam_dosya']}\n")
        cikti.write(f"  Python Dosya  : {istatistik['python_dosya']}\n")
        cikti.write(f"  Dart Dosya    : {istatistik['dart_dosya']}\n")
        cikti.write(f"  Toplam Satır  : {istatistik['toplam_satir']}\n")
        if istatistik["hatali_dosya"]:
            cikti.write(f"  Hatalı Dosya  : {istatistik['hatali_dosya']} (okunamadı)\n")
        cikti.write(SEPARATOR_KALIN + "\n")

    return istatistik


def main():
    parser = argparse.ArgumentParser(
        description="Klasördeki .py ve .dart dosyalarını tek bir .txt'ye toplar.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("kaynak", help="Taranacak kaynak klasör yolu")
    parser.add_argument(
        "cikti", nargs="?", default=None,
        help="Çıktı .txt dosyasının adı (varsayılan: kod_ozeti_TARIH.txt)",
    )
    parser.add_argument(
        "--exclude", "-e", metavar="KLASOR", action="append", default=[],
        help="Ekstra atlanacak klasör adı (birden fazla kullanılabilir)",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.kaynak):
        print(f"[HATA] Klasör bulunamadı: {args.kaynak}")
        sys.exit(1)

    if args.cikti:
        cikti_yolu = args.cikti
    else:
        zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
        cikti_yolu = f"kod_ozeti_{zaman_damgasi}.txt"

    ekstra = {k.lower() for k in args.exclude}

    print(f"🔍 Taranıyor : {os.path.abspath(args.kaynak)}")
    print(f"🚫 Atlananlar: venv, site-packages, __pycache__, build, node_modules, "
          f".git, .dart_tool ... (+ pyvenv.cfg tespiti)")
    if ekstra:
        print(f"   + Ekstra   : {', '.join(sorted(ekstra))}")

    dosyalar = dosyalari_topla(args.kaynak, ekstra)

    if not dosyalar:
        print("⚠️  Hiç .py veya .dart dosyası bulunamadı.")
        sys.exit(0)

    print(f"📄 {len(dosyalar)} dosya bulundu "
          f"(Python: {sum(1 for d in dosyalar if d['dil']=='Python')}, "
          f"Dart: {sum(1 for d in dosyalar if d['dil']=='Dart')})")
    print(f"✍️  Yazılıyor : {cikti_yolu}")

    istatistik = cikti_yaz(dosyalar, cikti_yolu, args.kaynak, ekstra)

    boyut_kb = os.path.getsize(cikti_yolu) / 1024
    print(f"\n✅ Tamamlandı!")
    print(f"   Dosya        : {cikti_yolu}")
    print(f"   Boyut        : {boyut_kb:.1f} KB")
    print(f"   Toplam Satır : {istatistik['toplam_satir']}")
    if istatistik["hatali_dosya"]:
        print(f"   ⚠️  {istatistik['hatali_dosya']} dosya okunamadı.")


if __name__ == "__main__":
    main()
