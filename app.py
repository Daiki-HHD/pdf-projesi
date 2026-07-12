import os, uuid
from flask import Flask, request, render_template, send_file
from pypdf import PdfReader, PdfWriter

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1 GB Sınırı
UPLOAD_FOLDER = 'temp_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def parse_pages(page_str):
    pages_to_keep = set()
    if not page_str.strip(): return pages_to_keep
    
    for part in page_str.split(','):
        part = part.strip()
        if '-' in part:
            try:
                s, e = map(int, part.split('-'))
                for i in range(s, e + 1):
                    pages_to_keep.add(i - 1)  # 0 tabanlı indeks için -1
            except ValueError:
                continue
        else:
            try:
                pages_to_keep.add(int(part) - 1)
            except ValueError:
                continue
    return pages_to_keep

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('pdf_file')
        if not file or file.filename == '': return "Dosya seçilmedi!", 400
        
        uid = str(uuid.uuid4())
        in_path = os.path.join(UPLOAD_FOLDER, f'{uid}_in.pdf')
        out_path = os.path.join(UPLOAD_FOLDER, f'{uid}_out.pdf')
        file.save(in_path)

        try:
            reader = PdfReader(in_path)
            writer = PdfWriter()
            total_pages = len(reader.pages)
            
            # Kullanıcının seçtiği (kalmasını istediği) sayfaları alıyoruz
            pages_to_keep = parse_pages(request.form.get('pages', ''))
            
            # Sadece seçilen sayfaları yeni PDF'e ekle
            for i in range(total_pages):
                if i in pages_to_keep:
                    writer.add_page(reader.pages[i])
            
            # Eğer girilen aralık dosya sayfa sayısıyla tamamen alakasızsa ve boş kaldıysa hata verme kontrolü
            if len(writer.pages) == 0:
                return "Hata: Belirttiğiniz sayfa aralığı mevcut PDF'te bulunamadı veya hiçbir sayfa seçilmedi!", 400
            
            with open(out_path, 'wb') as f:
                writer.write(f)
                
            return send_file(out_path, as_attachment=True, download_name=f"Secilenler_{file.filename}")
        except Exception as e:
            return f"Sunucu Hatası: {str(e)}", 500
        finally:
            # İşlem bitince sunucu temizliği (isteğe bağlı eklenebilir)
            pass
            
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
