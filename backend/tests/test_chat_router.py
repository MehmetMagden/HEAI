import pytest
from fastapi.testclient import TestClient
from main import app  # main.py dosyanızdaki FastAPI app objesini import edin

# Testler için TestClient oluşturuluyor
client = TestClient(app)

# Test senaryoları: (girdi_context, beklenen_sources_listesi)
test_scenarios = [
    # 1. Kaynak Olmayan Durum
    ("Bu metinde herhangi bir kaynak bilgisi yoktur.", []),
    # 2. Tek Kaynak Durumu
    ("Cevap, [Pırlanta Serisi 1] kitabından alınmıştır.", ["Pırlanta Serisi 1"]),
    # 3. Birden Fazla Benzersiz Kaynak Durumu
    ("Bu konu hem [Kırık Testi] içinde hem de [Asrın Getirdiği Tereddütler 4] kitabında geçer.", ["Kırık Testi", "Asrın Getirdiği Tereddütler 4"]),
    # 4. Tekrarlayan (Duplicate) Kaynak Durumu
    ("Kaynak olarak [Fasıldan Fasıla 2] gösterilebilir. Evet, kesinlikle [Fasıldan Fasıla 2] en doğru kaynaktır.", ["Fasıldan Fasıla 2"]),
    # 5. Karışık Durum (Benzersiz ve Tekrarlayan)
    ("Önce [Sonsuz Nur] okunmalı, sonra [Kalbin Zümrüt Tepeleri]. Tekrar etmek gerekirse [Sonsuz Nur] temel bir eserdir.", ["Sonsuz Nur", "Kalbin Zümrüt Tepeleri"]),
    # 6. Boş Context Durumu
    ("", []),
    # 7. Bitişik kaynaklar ve metin içi kaynaklar
    ("Metin[Kaynak1]metin[Kaynak2] devam ediyor. [Kaynak1] tekrar ediyor.", ["Kaynak1", "Kaynak2"]),
]

@pytest.mark.parametrize("mock_context, expected_sources", test_scenarios)
def test_send_message_source_extraction(mocker, mock_context, expected_sources):
    """
    /message endpoint'inin RAG context'inden kaynakları doğru bir şekilde
    ayıklayıp tekilleştirdiğini test eder.
    """
    # --- Bağımlılıkları Mock'lama (Taklit Etme) ---
    # rag_service.retrieve_context fonksiyonunu mock'layarak önceden tanımlı context döndürmesini sağlıyoruz.
    mocker.patch('routers.chat.rag_service.retrieve_context', return_value=mock_context)
    
    # LLM ve emotion servislerinin testle ilgisi olmadığı için basit birer değer döndürmelerini sağlıyoruz.
    mocker.patch('routers.chat.llm_service.chat', return_value="Bu bir test cevabıdır.")
    mocker.patch('routers.chat.detect_emotion', return_value="huzur")

    # --- API İsteği ---
    # Test edilecek endpoint'e POST isteği gönderiyoruz.
    request_payload = {
        "message": "Test sorusu",
        "history": [],
        "use_rag": True,
        "stream": False
    }
    response = client.post("/chat/message", json=request_payload) # Router prefix'ini ekleyin (ör: /chat)

    # --- Doğrulama (Assertion) ---
    # Yanıtın başarılı (200 OK) olduğunu kontrol et
    assert response.status_code == 200
    
    # Yanıtın JSON gövdesini al
    response_data = response.json()
    
    # 'sources' alanının beklenen değerle eşleştiğini kontrol et
    assert "sources" in response_data
    assert response_data["sources"] == expected_sources
    
    # Yanıt metninden kaynakların temizlendiğini de kontrol edebiliriz.
    assert "cleaned_response_text" not in response_data["text"] # Modelin kendisi kaynak üretmediyse
    print(f"✅ Test Başarılı: Context='{mock_context[:30]}...' -> Beklenen={expected_sources}, Gelen={response_data['sources']}")
