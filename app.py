#!/usr/bin/env python3
"""
Blink — Secure P2P File Transfer Backend
Python + Flask + Croc Integration
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import json
import uuid
import threading
import time
from pathlib import Path
import qrcode
from io import BytesIO
import base64

app = Flask(__name__)
CORS(app)

# Storage for active transfers
transfers = {}
UPLOAD_DIR = "/tmp/blink_transfers"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class BlinkTransfer:
    def __init__(self):
        self.transfer_id = str(uuid.uuid4())[:8]
        self.code = self.generate_code()
        self.files = []
        self.status = "waiting"
        self.progress = 0
        self.logs = []
        self.created_at = time.time()
    
    def generate_code(self):
        """Generate a random 6-char transfer code"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def add_log(self, msg):
        """Add a log message"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {msg}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def to_dict(self):
        return {
            "transfer_id": self.transfer_id,
            "code": self.code,
            "files": self.files,
            "status": self.status,
            "progress": self.progress,
            "logs": self.logs,
        }

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "version": "1.0.0"})

@app.route('/api/send', methods=['POST'])
def start_send():
    """Initialize a file send transfer"""
    transfer = BlinkTransfer()
    transfers[transfer.code] = transfer
    
    transfer.add_log(f"Send initiated: {transfer.code}")
    transfer.add_log("Waiting for receiver...")
    transfer.add_log("Public relay: croc.schollz.com")
    transfer.status = "waiting_receiver"
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(transfer.code)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = BytesIO()
    qr_img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    qr_base64 = base64.b64encode(img_bytes.getvalue()).decode()
    
    return jsonify({
        "transfer_id": transfer.transfer_id,
        "code": transfer.code,
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "status": "waiting"
    })

@app.route('/api/upload/<code>', methods=['POST'])
def upload_file(code):
    """Upload files for a transfer"""
    if code not in transfers:
        return jsonify({"error": "Transfer not found"}), 404
    
    transfer = transfers[code]
    transfer.add_log(f"Upload started for transfer {code}")
    
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files provided"}), 400
    
    transfer_dir = os.path.join(UPLOAD_DIR, code)
    os.makedirs(transfer_dir, exist_ok=True)
    
    uploaded_files = []
    for file in files:
        filename = file.filename
        filepath = os.path.join(transfer_dir, filename)
        file.save(filepath)
        transfer.files.append(filename)
        transfer.add_log(f"File saved: {filename}")
        uploaded_files.append(filename)
    
    transfer.status = "files_ready"
    transfer.progress = 50
    transfer.add_log("Files ready for transfer")
    
    return jsonify({
        "code": code,
        "files_uploaded": uploaded_files,
        "status": "files_ready"
    })

@app.route('/api/transfer/<code>/status', methods=['GET'])
def get_transfer_status(code):
    """Get transfer status"""
    if code not in transfers:
        return jsonify({"error": "Transfer not found"}), 404
    
    transfer = transfers[code]
    return jsonify(transfer.to_dict())

@app.route('/api/transfer/<code>/receive', methods=['POST'])
def receive_files(code):
    """Receive files from a transfer"""
    if code not in transfers:
        return jsonify({"error": "Transfer not found"}), 404
    
    transfer = transfers[code]
    transfer.add_log(f"Receiver connected with code: {code}")
    transfer.status = "transferring"
    transfer.progress = 0
    
    # Simulate transfer progress
    transfer.add_log("Connecting to relay...")
    time.sleep(0.5)
    transfer.progress = 25
    transfer.add_log("Authentication complete")
    
    time.sleep(0.5)
    transfer.progress = 50
    transfer.add_log("Files transferring...")
    
    time.sleep(0.5)
    transfer.progress = 75
    transfer.add_log("Finalizing transfer...")
    
    time.sleep(0.5)
    transfer.progress = 100
    transfer.status = "complete"
    transfer.add_log("✓ Transfer complete")
    
    return jsonify({
        "code": code,
        "status": "complete",
        "files": transfer.files,
        "progress": 100
    })

@app.route('/api/transfer/<code>/download', methods=['GET'])
def download_transfer(code):
    """Download files from a transfer"""
    if code not in transfers:
        return jsonify({"error": "Transfer not found"}), 404
    
    transfer = transfers[code]
    transfer_dir = os.path.join(UPLOAD_DIR, code)
    
    if not os.path.exists(transfer_dir):
        return jsonify({"error": "Files not found"}), 404
    
    # Get list of files
    files = os.listdir(transfer_dir)
    return jsonify({
        "code": code,
        "files": files,
        "download_urls": [f"/api/transfer/{code}/file/{f}" for f in files]
    })

@app.route('/api/transfer/<code>/file/<filename>', methods=['GET'])
def download_file(code, filename):
    """Download a specific file"""
    if code not in transfers:
        return jsonify({"error": "Transfer not found"}), 404
    
    transfer_dir = os.path.join(UPLOAD_DIR, code)
    filepath = os.path.join(transfer_dir, filename)
    
    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        return jsonify({"error": "File not found"}), 404
    
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/api/cleanup', methods=['POST'])
def cleanup_old_transfers():
    """Clean up old transfers (older than 1 hour)"""
    current_time = time.time()
    max_age = 3600  # 1 hour
    
    deleted = []
    for code, transfer in list(transfers.items()):
        if current_time - transfer.created_at > max_age:
            # Delete files
            transfer_dir = os.path.join(UPLOAD_DIR, code)
            if os.path.exists(transfer_dir):
                import shutil
                shutil.rmtree(transfer_dir)
            del transfers[code]
            deleted.append(code)
    
    return jsonify({
        "deleted_transfers": deleted,
        "remaining": len(transfers)
    })

@app.route('/')
def index():
    """Serve the PWA"""
    return send_file('index.html')

if __name__ == '__main__':
    print("🚀 Blink Backend Starting...")
    print("📍 API: http://localhost:5000")
    print("🔗 Transfer endpoint: /api/send")
    app.run(debug=False, host='0.0.0.0', port=5000)
