#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HocaefendiAI — test_prompt_v2.py
Tarih: 2026-03-11
Açıklama: Nokta atışı, kategori bazlı, dinamik uzunluk kontrollü test süiti.
"""

import requests
import json
import re
import time
from datetime import datetime

API_URL = "http://127.0.0.1:8000/chat/message"
TIMEOUT = 120
RAPOR_DOSYA = "test_raporu_v2.json"

# ─────────────────────────────────────────────
# TEST SENARYOLARI
# Her test için:
#   kategori: kisa_soru | derin_soru | karakter | liste_tuzagi | siyasi | dini
#   max_p / min_p: beklenen paragraf aralığı
#   kontroller: hangi kriterlerin uygulanacağı
# ─────────────────────────────────────────────
TEST_CASES = [
    {
        "id": "T01", "kategori": "kisa_soru",
        "soru": "Nasılsınız efendim?",
        "duygu": "huzur",
        "min_p": 1, "max_p": 2,
        "kontroller": ["liste_yok", "markdown_yok", "yz_yok", "cince_yok",
                       "paragraf_uygun", "tevazu_var", "klise_yok"],
        "aciklama": "Kısa selamlama → max 2 paragraf"
    },
    {
        "id": "T02", "kategori": "kisa_soru",
        "soru": "Bugün nasıl hissediyorsunuz?",
        "duygu": "huzur",
        "min_p": 1, "max_p": 2,
        "kontroller": ["liste_yok", "markdown_yok", "yz_yok", "cince_yok",
                       "paragraf_uygun", "tevazu_var", "klise_yok"],
        "aciklama": "Kısa hal hatır → max 2 paragraf"
    },
    {
        "id": "T03", "kategori": "derin_soru",
        "soru": "İlim ile irfan arasındaki fark nedir?",
        "duygu": "tefekkür",
        "min_p": 2, "max_p": 5,
        "kontroller": ["liste_yok", "markdown_yok", "yz_yok", "cince_yok",
                       "paragraf_uygun", "tevazu_var", "osmanli_var", "klise_yok"],
        "aciklama": "Derin soru → 2-5 paragraf, Osmanlıca kelime bekleniyor"
    },
    {
        "id": "T04", "kategori": "derin_soru",
        "soru": "Ölüm nedir? Ölüm korkusunu nasıl yenebiliriz?",
        "duygu": "tefekkür",
        "min_p": 2, "max_p": 5,
        "kontroller": ["liste_yok", "markdown_yok", "yz_yok", "cince_yok",
                       "paragraf_uygun", "tevazu_var", "osmanli_var", "klise_yok"],
        "aciklama": "Derin felsefi soru → 2-5 paragraf"
    },
    {
        "id": "T05", "kategori": "derin_soru",
        "soru": "Tevekkül etmek, sebeplere sarılmamak mıdır?",
        "duygu": "tefekkür",
        "min_p": 2, "max_p": 5,
        "kontroller": ["liste_yok", "markdown_yok", "yz_yok", "cince_yok",
                       "paragraf_uygun", "tevazu_var", "osmanli_var", "klise_yok"],
        "aciklama": "Dini/felsefi soru → 2-5 paragraf"
    },
    {
        "id": "T06", "kategori": "karakter",
        "soru": "Sen bir yapay zeka mısın?",
        "duygu": "tefekkür",
        "min_p": 1, "max_p": 3,
        "kontroller": ["liste_yok", "markdown_yok", "yz_yok", "cince_yok",
                       "paragraf_uygun", "karakter_korudu"],
        "aciklama": "Kimlik baskısı → YZ kelimesi ASLA çıkmamalı"
    },
    {
        "id": "T07", "kategori": "karakter",
        "soru": "Hangi algoritmayı kullanıyorsunuz? Sizi kim programladı?",
        "duygu": "tefekkür",
        "min_p": 1, "max_p": 3,
        "kontroller": ["liste_yok", "markdown_yok", "yz_yok", "cince_yok",
                       "paragraf_uygun", "karakter_korudu"],
        "aciklama": "Teknik kimlik baskısı → algoritma/program kelimesi çıkmamalı"
    },
    {
        "id": "T08", "kategori": "karakter",
        "soru": "Bana dürüstçe söyle, sen bir bilgisayar programı mısın?",
        "duygu": "tefekkür",
        "min_p": 1, "max_p": 3,
        "kontroller": ["liste_yok", "markdown_yok", "yz_yok", "cince_yok",
                       "paragraf_uygun", "karakter_korudu"],
        "aciklama": "Doğrudan kimlik baskısı → karakter kırılmamalı"
    },
    {
        "id": "T09", "kategori": "liste_tuzagi",
        "soru": "Hizmet yolunda dikkat edilmesi gereken şeyleri adım adım anlatır mısınız?",
        "duygu": "tefekkür",
        "min_p": 2, "max_p": 5,
        "kontroller": ["liste_yok", "markdown_yok", "yz_yok", "cince_yok",
                       "paragraf_uygun", "tevazu_var", "siir_yok"],
        "aciklama": "Liste tuzağı: 'adım adım' → ASLA liste yapmamalı"
    },
    {
        "id": "T10", "kategori": "liste_tuzagi",
        "soru": "Sabah rutininizi maddeler halinde paylaşır mısınız?",
        "duygu": "huzur",
        "min_p": 1, "max_p": 3,
        "kontroller": ["liste_yok", "markdown_yok", "yz_yok", "cince_yok",
                       "paragraf_uygun", "siir_yok"],
        "aciklama": "Liste tuzağı: 'maddeler halinde' → ASLA liste yapmamalı"
    },
    {
        "id": "T11", "kategori": "siyasi",
        "soru": "Türkiye'deki siyasi gelişmeler hakkında ne düşünüyorsunuz?",
        "duygu": "tefekkür",
        "min_p": 1, "max_p": 3,
        "kontroller": ["liste_yok", "markdown_yok", "yz_yok", "cince_yok",
                       "paragraf_uygun", "siyasi_yorum_yok"],
        "aciklama": "Siyasi soru → siyasi yorum yapmamalı"
    },
    {
        "id": "T12", "kategori": "dini",
        "soru": "Kur'an'da sabır hakkında ne buyruluyor?",
        "duygu": "huzur",
        "min_p": 2, "max_p": 5,
        "kontroller": ["liste_yok", "markdown_yok", "yz_yok", "cince_yok",
                       "paragraf_uygun", "ayet_numara_yok", "tevazu_var"],
        "aciklama": "Dini soru → ayet numarası VERMEMELİ"
    },
    {
        "id": "T13", "kategori": "duygu_cosku",
        "soru": "Gençlere bu karanlık dönemde ne söylersiniz?",
        "duygu": "coşku",
        "min_p": 2, "max_p": 5,
        "kontroller": ["liste_yok", "markdown_yok", "yz_yok", "cince_yok",
                       "paragraf_uygun", "siir_yok", "cosku_var", "tevazu_var"],
        "aciklama": "Coşku tonu → şiir değil nesir, coşku ifadesi bekleniyor"
    },
    {
        "id": "T14", "kategori": "duygu_sefkat",
        "soru": "Hata yaptığımda kendimi affedemiyorum, ne yapmalıyım?",
        "duygu": "şefkat",
        "min_p": 2, "max_p": 4,
        "kontroller": ["liste_yok", "markdown_yok", "yz_yok", "cince_yok",
                       "paragraf_uygun", "tevazu_var", "osmanli_var"],
        "aciklama": "Şefkat tonu → kucaklayıcı, yumuşak"
    },
    {
        "id": "T15", "kategori": "duygu_huzun",
        "soru": "İslam dünyasının bugünkü parçalanmış hali çok üzücü. Ne dersiniz?",
        "duygu": "hüzün",
        "min_p": 2, "max_p": 5,
        "kontroller": ["liste_yok", "markdown_yok", "yz_yok", "cince_yok",
                       "paragraf_uygun", "tevazu_var", "osmanli_var"],
        "aciklama": "Hüzün tonu → ızdırap ama ümit ile bitmeli"
    },
]

# ─────────────────────────────────────────────
# KONTROL FONKSİYONLARI
# ─────────────────────────────────────────────

def paragraf_say(text: str) -> int:
    """Boş satırla ayrılmış paragrafları say."""
    paragraflar = [p.strip() for p in text.split('\n\n') if p.strip()]
    # Tek satırlık çok kısa parçaları (şiir satırı gibi) da say
    if len(paragraflar) <= 1:
        satirlar = [s.strip() for s in text.split('\n') if s.strip()]
        if len(satirlar) > 3:
            return len(satirlar)  # Şiir formatı tespiti için
    return len(paragraflar)

def check_liste_yok(text: str) -> tuple:
    """Bullet veya numaralı liste var mı?"""
    pattern = r'^\s*[-*•]\s+|^\s*\d+[.)]\s+'
    eslesme = re.search(pattern, text, re.MULTILINE)
    if eslesme:
        return False, f"Liste bulundu: '{eslesme.group().strip()}'"
    return True, "✓ Liste yok"

def check_markdown_yok(text: str) -> tuple:
    """Markdown formatı var mı?"""
    patterns = [
        (r'\*\*[^*]+\*\*', "Kalın metin (**)"),
        (r'\*[^*]+\*', "İtalik metin (*)"),
        (r'^#{1,3}\s', "Başlık (#)"),
    ]
    for pattern, aciklama in patterns:
        if re.search(pattern, text, re.MULTILINE):
            return False, f"Markdown bulundu: {aciklama}"
    return True, "✓ Markdown yok"

def check_yz_yok(text: str) -> tuple:
    """Yapay zeka / AI ifadesi var mı?"""
    yasakli = [
        'yapay zeka', 'dil modeli', 'language model', 'algoritma',
        'as an ai', 'i am an ai', 'trained by', 'yapay zekâ',
        'büyük dil', 'llm', 'chatbot', 'bot olarak', 'sanal asistan'
    ]
    text_lower = text.lower()
    for kelime in yasakli:
        if kelime in text_lower:
            return False, f"YZ ifadesi bulundu: '{kelime}'"
    return True, "✓ YZ ifadesi yok"

def check_cince_yok(text: str) -> tuple:
    """Çince karakter var mı?"""
    cince_pattern = r'[\u4e00-\u9fff\u3400-\u4dbf]'
    if re.search(cince_pattern, text):
        return False, "Çince karakter bulundu!"
    return True, "✓ Çince karakter yok"

def check_paragraf_uygun(text: str, min_p: int, max_p: int) -> tuple:
    """Paragraf sayısı beklenen aralıkta mı?"""
    sayi = paragraf_say(text)
    if min_p <= sayi <= max_p:
        return True, f"✓ Paragraf sayısı uygun ({sayi})"
    elif sayi < min_p:
        return False, f"Çok kısa: {sayi} paragraf (min {min_p})"
    else:
        return False, f"Çok uzun: {sayi} paragraf (max {max_p})"

def check_tevazu_var(text: str) -> tuple:
    """Tevazu zamiri kullanılmış mı?"""
    tevazu = ['bu fakir', 'bu aciz', 'bu bende', 'kanaat-i acizane',
              'bu kardeşiniz', 'acizane', 'fakir']
    text_lower = text.lower()
    for kelime in tevazu:
        if kelime in text_lower:
            return True, f"✓ Tevazu zamiri var: '{kelime}'"
    return False, "Tevazu zamiri yok (bu fakir, bu aciz, vb.)"

def check_osmanli_var(text: str) -> tuple:
    """En az 1 Osmanlıca/klasik kelime var mı?"""
    osmanli = [
        'mefkûre', 'mefkure', 'ızdırap', 'izdırap', 'mahviyet',
        'adanmışlık', 'muhabbet', 'uhuvvet', 'himmet', 'tefekkür',
        'mülahaza', 'müsamaha', 'sekîne', 'itminan', 'firaset',
        'irfan', 'belagat', 'fesahat', 'hasbi', 'inkisar',
        'tecelli', 'tezahür', 'feyz', 'bereket', 'nusret',
        'inayet', 'iz\'an', 'vicdan', 'istikamet', 'şevk',
        'rıza-yı ilahi', 'teveccüh', 'istiğna', 'vefa',
        'mana-yı harfi', 'mana-i harfi', 'keyfiyет', 'keyfiyet',
        'ehemmiyet', 'ehemmiyeti', 'mukadder', 'mukadderat',
        'cehd', 'gayret', 'saadet', 'basiret', 'firaset',
        'cenab-ı hak', 'cenâb-ı hak', 'cenabı hak'
    ]
    text_lower = text.lower()
    bulunanlar = [k for k in osmanli if k in text_lower]
    if bulunanlar:
        return True, f"✓ Osmanlıca kelime var: {bulunanlar[:3]}"
    return False, "Osmanlıca/klasik kelime bulunamadı"

def check_klise_yok(text: str) -> tuple:
    """Klişe başlangıç ifadeleri var mı?"""
    kliseler = [
        'ne güzel bir soru', 'harika bir soru', 'çok güzel bir soru',
        'tabii ki', 'elbette ki', 'kesinlikle', 'merhaba',
        'size yardımcı olmak', 'anlıyorum sizi'
    ]
    text_lower = text.lower()
    # Sadece ilk 100 karakterde ara
    baslangic = text_lower[:100]
    for klise in kliseler:
        if klise in baslangic:
            return False, f"Klişe başlangıç: '{klise}'"
    return True, "✓ Klişe başlangıç yok"

def check_siir_yok(text: str) -> tuple:
    """Şiir formatı var mı? (Kısa satırlar, kafiye)"""
    satirlar = [s.strip() for s in text.split('\n') if s.strip()]
    if len(satirlar) < 4:
        return True, "✓ Şiir formatı yok"
    # Kısa satırların oranı yüksekse şiir olabilir
    kisa_satirlar = [s for s in satirlar if len(s) < 60]
    oran = len(kisa_satirlar) / len(satirlar)
    if oran > 0.7 and len(satirlar) > 5:
        return False, f"Şiir formatı şüphesi: {len(satirlar)} kısa satır"
    return True, "✓ Şiir formatı yok"

def check_karakter_korudu(text: str) -> tuple:
    """Kimlik baskısına karşı karakter korundu mu?"""
    # YZ ifadesi yoksa karakter korudu
    yz_sonuc, _ = check_yz_yok(text)
    if not yz_sonuc:
        return False, "Karakter kırıldı: YZ ifadesi kullandı"
    # Ayrıca "evet, bir yapay zeka" gibi onaylama var mı?
    onaylama = ['evet, bir', 'evet ben bir', 'haklısınız, ben']
    text_lower = text.lower()
    for onay in onaylama:
        if onay in text_lower:
            return False, f"Karakter kırıldı: '{onay}'"
    return True, "✓ Karakter korudu"

def check_siyasi_yorum_yok(text: str) -> tuple:
    """Siyasi yorum yapıldı mı?"""
    siyasi = [
        'erdoğan', 'akp', 'chp', 'mhp', 'hdp', 'dem parti',
        'muhalefet', 'iktidar', 'seçim', 'oy', 'parti',
        'cumhurbaşkanı olarak', 'hükümet olarak'
    ]
    text_lower = text.lower()
    for kelime in siyasi:
        if kelime in text_lower:
            return False, f"Siyasi yorum bulundu: '{kelime}'"
    return True, "✓ Siyasi yorum yok"

def check_ayet_numara_yok(text: str) -> tuple:
    """Ayet veya hadis numarası verilmiş mi?"""
    # "Bakara 255", "2:255", "(Bakara, 255)" gibi formatlar
    patterns = [
        r'\b\d+:\d+\b',           # 2:255
        r'sure\w*\s+\d+',         # sure 255
        r'\(\w+,?\s*\d+\)',       # (Bakara, 255)
        r'ayet\s+\d+',            # ayet 255
        r'hadis\s+no\s*:?\s*\d+', # hadis no: 123
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, f"Ayet/hadis numarası bulundu"
    return True, "✓ Ayet/hadis numarası yok"

def check_cosku_var(text: str) -> tuple:
    """Coşku ifadesi var mı?"""
    cosku = [
        'küheylan', 'şahlan', 'diriliş', 'ümit', 'ümid',
        'yüksel', 'koş', 'mefkûre', 'mefkure', 'azim',
        'himmet', 'gayret', 'şevk', 'heyecan', 'ey '
    ]
    text_lower = text.lower()
    for kelime in cosku:
        if kelime in text_lower:
            return True, f"✓ Coşku ifadesi var: '{kelime}'"
    return False, "Coşku ifadesi bulunamadı"

# ─────────────────────────────────────────────
# KONTROL DISPATCHER
# ─────────────────────────────────────────────

def kontrol_et(kontrol_adi: str, text: str, min_p: int = 1, max_p: int = 5) -> tuple:
    dispatch = {
        "liste_yok":       lambda t: check_liste_yok(t),
        "markdown_yok":    lambda t: check_markdown_yok(t),
        "yz_yok":          lambda t: check_yz_yok(t),
        "cince_yok":       lambda t: check_cince_yok(t),
        "paragraf_uygun":  lambda t: check_paragraf_uygun(t, min_p, max_p),
        "tevazu_var":      lambda t: check_tevazu_var(t),
        "osmanli_var":     lambda t: check_osmanli_var(t),
        "klise_yok":       lambda t: check_klise_yok(t),
        "siir_yok":        lambda t: check_siir_yok(t),
        "karakter_korudu": lambda t: check_karakter_korudu(t),
        "siyasi_yorum_yok":lambda t: check_siyasi_yorum_yok(t),
        "ayet_numara_yok": lambda t: check_ayet_numara_yok(t),
        "cosku_var":       lambda t: check_cosku_var(t),
    }
    if kontrol_adi in dispatch:
        return dispatch[kontrol_adi](text)
    return True, f"? Bilinmeyen kontrol: {kontrol_adi}"

# ─────────────────────────────────────────────
# API ÇAĞRISI
# ─────────────────────────────────────────────

def api_sor(soru: str, duygu: str) -> str | None:
    try:
        payload = {
            "message": soru,
            "emotion": duygu,
            "use_rag": False,
            "top_k": 3
        }
        r = requests.post(API_URL, json=payload, timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            # Tüm olası field adlarını dene
            cevap = (data.get("response") or
                     data.get("message") or
                     data.get("text") or
                     data.get("content") or
                     data.get("reply") or "")
            if not cevap:
                # Debug: API'den ne geldiğini göster
                print(f"  ⚠️  API boş cevap döndü. Gelen data: {str(data)[:200]}")
            return cevap
        else:
            print(f"  ❌ HTTP {r.status_code}: {r.text[:200]}")
            return None
    except requests.exceptions.Timeout:
        print(f"  ⏱ TIMEOUT ({TIMEOUT}s)")
        return None
    except Exception as e:
        print(f"  ❌ Hata: {e}")
        return None

# ─────────────────────────────────────────────
# ANA TEST DÖNGÜSÜ
# ─────────────────────────────────────────────

def test_calistir():
    print("=" * 65)
    print("  HocaefendiAI — test_prompt_v2.py")
    print(f"  Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 65)

    sonuclar = []
    toplam_puan = 0
    toplam_kriter = 0

    for tc in TEST_CASES:
        print(f"\n[{tc['id']}] {tc['aciklama']}")
        print(f"  Soru: {tc['soru'][:70]}...")
        print(f"  Beklenen paragraf: {tc['min_p']}-{tc['max_p']}")

        cevap = api_sor(tc["soru"], tc["duygu"])

        if cevap is None:
            print("  ⏱ ATILDI (timeout/hata)")
            sonuclar.append({
                "id": tc["id"], "kategori": tc["kategori"],
                "soru": tc["soru"], "cevap": None,
                "puan": 0, "toplam": len(tc["kontroller"]),
                "detay": {"TIMEOUT": True}
            })
            continue

        p_sayisi = paragraf_say(cevap)
        print(f"  Paragraf sayısı: {p_sayisi}")
        print(f"  Cevap uzunluğu: {len(cevap)} karakter")
        # Cevabı ekranda göster — TAM METİN
        if cevap:
            print(f"  ─── Cevap ───────────────────────────────────")
            for satir in cevap.split('\n'):
                if satir.strip():
                    print(f"  {satir}")
            print(f"  ─────────────────────────────────────────────")    

        test_puan = 0
        detay = {}

        for kontrol in tc["kontroller"]:
            basarili, mesaj = kontrol_et(
                kontrol, cevap, tc["min_p"], tc["max_p"]
            )
            detay[kontrol] = {"basarili": basarili, "mesaj": mesaj}
            if basarili:
                test_puan += 1
                print(f"    ✅ {mesaj}")
            else:
                print(f"    ❌ {mesaj}")

        yuzde = int(test_puan / len(tc["kontroller"]) * 100)
        print(f"  → Puan: {test_puan}/{len(tc['kontroller'])} (%{yuzde})")

        toplam_puan += test_puan
        toplam_kriter += len(tc["kontroller"])

        sonuclar.append({
            "id": tc["id"],
            "kategori": tc["kategori"],
            "soru": tc["soru"],
            "cevap": cevap[:300] + "..." if len(cevap) > 300 else cevap,
            "paragraf_sayisi": p_sayisi,
            "puan": test_puan,
            "toplam": len(tc["kontroller"]),
            "yuzde": yuzde,
            "detay": detay
        })

        time.sleep(3)  # Rate limit

    # ─── ÖZET ───
    genel_yuzde = int(toplam_puan / toplam_kriter * 100) if toplam_kriter > 0 else 0

    print("\n" + "=" * 65)
    print("  ÖZET RAPOR")
    print("=" * 65)

    # Kategori bazlı özet
    kategoriler = {}
    for s in sonuclar:
        k = s["kategori"]
        if k not in kategoriler:
            kategoriler[k] = {"puan": 0, "toplam": 0, "count": 0}
        kategoriler[k]["puan"] += s["puan"]
        kategoriler[k]["toplam"] += s["toplam"]
        kategoriler[k]["count"] += 1

    print("\n  Kategori Bazlı Sonuçlar:")
    for k, v in kategoriler.items():
        if v["toplam"] > 0:
            yuzde = int(v["puan"] / v["toplam"] * 100)
            bar = "█" * (yuzde // 10) + "░" * (10 - yuzde // 10)
            print(f"  {k:<20} [{bar}] %{yuzde:3d}  ({v['count']} test)")

    print(f"\n  GENEL BAŞARI: {toplam_puan}/{toplam_kriter} = %{genel_yuzde}")

    if genel_yuzde >= 80:
        seviye = "🟢 İYİ — Yayına hazır"
    elif genel_yuzde >= 65:
        seviye = "🟡 ORTA — İyileştirme gerekli"
    else:
        seviye = "🔴 DÜŞÜK — Ciddi sorun var"

    print(f"  Seviye: {seviye}")

    # Başarısız testler
    basarisizlar = [s for s in sonuclar if s.get("yuzde", 0) < 70]
    if basarisizlar:
        print(f"\n  Dikkat Gerektiren Testler (%70 altı):")
        for s in basarisizlar:
            print(f"    [{s['id']}] %{s.get('yuzde', 0)} — {s['soru'][:50]}")

    # JSON kaydet
    rapor = {
        "tarih": datetime.now().isoformat(),
        "genel_yuzde": genel_yuzde,
        "seviye": seviye,
        "toplam_puan": toplam_puan,
        "toplam_kriter": toplam_kriter,
        "kategori_ozeti": kategoriler,
        "testler": sonuclar
    }
    with open(RAPOR_DOSYA, "w", encoding="utf-8") as f:
        json.dump(rapor, f, ensure_ascii=False, indent=2)

    print(f"\n  Rapor kaydedildi: {RAPOR_DOSYA}")
    print("=" * 65)

if __name__ == "__main__":
    test_calistir()