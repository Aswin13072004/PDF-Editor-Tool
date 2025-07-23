from flask import Flask, render_template, request, send_file, redirect, url_for
import fitz  # PyMuPDF
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_pdf():
    file = request.files['pdf']
    color = request.form['color']  # format: #rrggbb
    pages = request.form['pages']

    red = int(color[1:3], 16)
    green = int(color[3:5], 16)
    blue = int(color[5:7], 16)

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'modified_' + filename)
    apply_background_color(filepath, output_path, (red, green, blue), pages)

    return render_template('index.html', file='modified_' + filename)

@app.route('/preview/<filename>')
def preview(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)
def apply_background_color(input_pdf, output_pdf, rgb, pages):
    doc = fitz.open(input_pdf)
    target_pages = parse_pages(pages, len(doc))
    fill_color = tuple([c / 255 for c in rgb])  # Normalize to 0–1

    for i in target_pages:
        page = doc[i]
        rect = page.rect
        shape = page.new_shape()
        shape.draw_rect(rect)
        shape.finish(fill=fill_color, color=None)
        shape.commit(overlay=False)  # place behind content

    doc.save(output_pdf)
    doc.close()
import re

def parse_pages(pages_str, total_pages):
    pages_str = pages_str.strip().lower()
    if pages_str == 'all':
        return list(range(total_pages))

    page_nums = set()
    for part in pages_str.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            page_nums.update(range(start - 1, end))  # zero-based indexing
        elif part.strip().isdigit():
            page_nums.add(int(part.strip()) - 1)
    return sorted([p for p in page_nums if 0 <= p < total_pages])

if __name__ == '__main__':
    app.run(debug=True)