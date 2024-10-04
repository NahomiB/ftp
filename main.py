from flask import Flask, request, jsonify, send_file
import os

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file:
        filename = file.filename
        file.save(os.path.join('uploads', filename))
        return jsonify({'message': 'File uploaded successfully'}), 201

@app.route('/download', methods=['GET'])
def download_file():
    filename = request.args.get('filename')
    if filename is None:
        return jsonify({'message': 'No filename specified'}), 400

    if os.path.exists(os.path.join('uploads', filename)):
        return send_file(os.path.join('uploads', filename), as_attachment=True)
    else:
        return jsonify({'message': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)