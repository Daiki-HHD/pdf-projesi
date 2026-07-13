from flask import Flask, render_template, send_file
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Yüklediğin ikonu uygulamaya tanıtan yeni yol
@app.route('/icon.png')
def serve_icon():
    return send_file('icon.png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
