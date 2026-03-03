# verify_db.py
import chromadb

# Kalıcı depolama için client oluştur
client = chromadb.PersistentClient(path="./data/chroma_db")

try:
    # Koleksiyonu al
    collection = client.get_collection(name="hocaefendi_books") # Koleksiyon adınız farklıysa güncelleyin
    
    # Koleksiyondaki toplam doküman sayısını yazdır
    print(f"ChromaDB'de toplam {collection.count()} adet doküman parçası (chunk) bulundu.")
    
except ValueError:
    print("Koleksiyon bulunamadı. Lütfen koleksiyon adını kontrol edin.")