import os, uuid
from flask import Flask, request, render_template, send_file
import fitz  # Hızlı işlem yapan PyMuPDF kütüphanesi

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1 GB Sınırı
UPLOAD_FOLDER = 'temp_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def parse_pages(page_str, total_pages):
    pages_to_keep = set()
    if not page_str.strip(): return pages_to_keep
    
    for part in page_str.split(','):
        part = part.strip()
        if '-' in part:
            try:
                s, e = map(int, part.split('-'))
                for i in range(s, e + 1):
                    if 1 <= i <= total_pages:
                        pages_to_keep.add(i - 1)
            except ValueError:
                continue
        else:
            try:
                p = int(part)
                if 1 <= p <= total_pages:
                    pages_to_keep.add(p - 1)
            except ValueError:
                continue
    # PyMuPDF select() işlemi için sıralı bir liste gerekiyor
    return sorted(list(pages_to_keep))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('pdf_file')
        if not file or file.filename == '': return "Dosya seçilmedi!", 400
        
        uid = str(uuid.uuid4())
        in_path = os.path.join(UPLOAD_FOLDER, f'{uid}_in.pdf')
        out_path = os.path.join(UPLOAD_FOLDER, f'{uid}_out.pdf')
        
        # Dosyayı sunucuya kaydet
        file.save(in_path)

        try:
            # PyMuPDF ile dosyayı aç (RAM'i yormadan diskten okur)
            doc = fitz.open(in_path)
            total_pages = len(doc)
            
            pages_to_keep = parse_pages(request.form.get('pages', ''), total_pages)
            
            if not pages_to_keep:
                doc.close()
                return "Hata: Belirttiğiniz sayfa aralığı mevcut PDF'te bulunamadı!", 400
            
            # Sadece seçilen sayfaları dosyada bırakır (İnanılmaz hızlı bir işlemdir)
            doc.select(pages_to_keep)
            
            # Yeni dosyayı optimize ederek kaydet ve kapat
            doc.save(out_path, garbage=3, deflate=True)
            doc.close()
            
            # HAYAT KURTARAN KISIM: 512MB RAM şişmesin diye ilk yüklenen orijinal dosyayı anında sil
            if os.path.exists(in_path):
                os.remove(in_path)
                
            return send_file(out_path, as_attachment=True, download_name=f"Secilenler_{file.filename}")
            
        except Exception as e:
            return f"Sunucu Hatası: {str(e)}", 500
            
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
