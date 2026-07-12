import os, uuid
from flask import Flask, request, render_template, send_file
from pypdf import PdfReader, PdfWriter

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  
UPLOAD_FOLDER = 'temp_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def parse_pages(page_str, total_pages):
    pages_to_delete = set()
    if not page_str.strip(): return pages_to_delete
    for part in page_str.split(','):
        part = part.strip()
        if '-' in part:
            s, e = map(int, part.split('-'))
            for i in range(s, e + 1):
                pages_to_delete.add(i - 1)
        else:
            pages_to_delete.add(int(part) - 1)
    return pages_to_delete

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('pdf_file')
        if not file or file.filename == '': return "Dosya yok!", 400
        
        uid = str(uuid.uuid4())
        in_path = os.path.join(UPLOAD_FOLDER, f'{uid}_in.pdf')
        out_path = os.path.join(UPLOAD_FOLDER, f'{uid}_out.pdf')
        file.save(in_path)

        try:
            reader = PdfReader(in_path)
            writer = PdfWriter()
            pages_to_del = parse_pages(request.form.get('pages', ''), len(reader.pages))
            
            for i in range(len(reader.pages)):
                if i not in pages_to_del:
                    writer.add_page(reader.pages[i])
            
            with open(out_path, 'wb') as f:
                writer.write(f)
                
            return send_file(out_path, as_attachment=True, download_name=f"Yeni_{file.filename}")
        except Exception as e:
            return str(e), 500
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
