import os, base64
from flask import Flask, request, render_template, send_file, jsonify
from PIL import Image
from io import BytesIO
from skimage import io, transform
from pyxelate import Pyx, Pal
from config import DEFAULT_CONFIG

app = Flask(__name__)

@app.route('/convert', methods=['GET'])
def show_form():
    """Display the upload form with current configuration"""
    return render_template(
        'upload.html',
        width=DEFAULT_CONFIG['width'],
        height=DEFAULT_CONFIG['height'],
        colors=DEFAULT_CONFIG['colors'],
        upload_endpoint_url=DEFAULT_CONFIG.get('upload_endpoint_url', '')
    )

@app.route('/convert', methods=['POST'])
def convert_image():
    """Handle image upload; either call external conversion API or run local conversion,
    then (optionally) upload converted BMP to provided endpoint and return JSON with base64 preview and upload response."""
    try:
        # Get form data
        width = int(request.form.get('width', DEFAULT_CONFIG['width']))
        height = int(request.form.get('height', DEFAULT_CONFIG['height']))
        upload_endpoint_url = request.form.get('upload_endpoint_url', '').strip()

        # Get colors from form
        colors = []
        for i in range(6):
            color_hex = request.form.get(f'color{i}', DEFAULT_CONFIG['colors'][i]).strip()
            colors.append(color_hex)

        # Get uploaded file
        if 'image' not in request.files:
            return jsonify({'error': 'No image file uploaded'}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # local conversion (existing behavior)
        my_pal = Pal.from_hex(colors)
        image = io.imread(file.stream)
        image = transform.resize(image, (height, width), anti_aliasing=True)
        image_p = Pyx(factor=1, palette=my_pal, dither="naive").fit_transform(image)
        pil_image = Image.fromarray(image_p.astype('uint8'))
        img_io = BytesIO()
        pil_image.save(img_io, format='BMP')
        img_io.seek(0)
        converted_bytes = img_io.read()

        # Prepare base64 preview
        b64 = base64.b64encode(converted_bytes).decode('ascii')
        data_url = f'data:image/bmp;base64,{b64}'

        # Return a data URL preview to the browser. Uploads to an external
        # endpoint should be performed from the browser (client-side) so the
        # user's local endpoints can be reached directly by their browser.
        result = {'preview': data_url}
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return '''
    <h1>Strict Color Dithering Server</h1>
    <p>Go to <a href="/convert">/convert</a> to use the image converter.</p>
    <p><strong>Guarantee:</strong> Only uses the 6 colors you specify - no unexpected colors!</p>
    '''

if __name__ == '__main__':
    app.run(debug=DEFAULT_CONFIG['debug'], host='0.0.0.0', port=DEFAULT_CONFIG['server_port'])
