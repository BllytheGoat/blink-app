#!/usr/bin/env python3
"""
Blink — Secure P2P File Transfer Backend
Python + Flask + Real Croc Integration
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
import shutil

app = Flask(__name__)
CORS(app)

# Storage for active transfers
transfers = {}
UPLOAD_DIR = "/tmp/blink_transfers"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Check if croc is available
CROC_BIN = shutil.which('croc')
if not CROC_BIN:
    print("⚠️  Warning: 'croc' not found in PATH. Install with: brew install croc (macOS) or apt install croc (Linux)")
    CROC_BIN = None

class BlinkTransfer:
    def __init__(self):
        self.transfer_id = str(uuid.uuid4())[:8]
        self.code = self.generate_code()
        self.files = []
        self.status = "waiting"
        self.progress = 0
        self.logs = []
        self.created_at = time.time()
        self.croc_process = None
    
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
    croc_status = "available" if CROC_BIN else "not_installed"
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "croc": croc_status
    })

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
    
    # Start Croc send in background
    if CROC_BIN:
        threading.Thread(target=start_croc_send, args=(transfer, transfer_dir), daemon=True).start()
    
    return jsonify({
        "code": code,
        "files_uploaded": uploaded_files,
        "status": "files_ready"
    })

def start_croc_send(transfer, transfer_dir):
    """Start Croc send process"""
    try:
        transfer.add_log("Starting Croc sender...")
        
        # Build croc send command with the transfer code
        files_to_send = [os.path.join(transfer_dir, f) for f in transfer.files]
        
        # croc send --code <code> file1 file2 ...
        cmd = [CROC_BIN, "send", "--code", transfer.code] + files_to_send
        
        transfer.add_log(f"Croc command: {' '.join(cmd)}")
        
        # Run croc send
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        transfer.croc_process = process
        transfer.status = "transferring"
        
        # Read output
        for line in process.stdout:
            line = line.strip()
            if line:
                transfer.add_log(line)
                if "Sending" in line or "sent" in line.lower():
                    transfer.progress = 75
        
        # Wait for process
        process.wait()
        
        if process.returncode == 0:
            transfer.progress = 100
            transfer.status = "complete"
            transfer.add_log("✓ Transfer complete via Croc")
        else:
            error = process.stderr.read()
            transfer.add_log(f"❌ Croc error: {error}")
            transfer.status = "error"
    
    except Exception as e:
        transfer.add_log(f"❌ Error starting Croc: {str(e)}")
        transfer.status = "error"

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
    
    if CROC_BIN:
        # Start Croc receive in background
        threading.Thread(target=start_croc_receive, args=(transfer, code), daemon=True).start()
        
        # Wait for transfer to complete (with timeout)
        for _ in range(60):  # 60 second timeout
            if transfer.status == "complete" or transfer.status == "error":
                break
            time.sleep(1)
    else:
        # Fallback: simulate transfer
        transfer.add_log("Croc not available, simulating transfer...")
        for i in range(0, 100, 20):
            time.sleep(0.5)
            transfer.progress = i
        transfer.progress = 100
        transfer.status = "complete"
        transfer.add_log("✓ Transfer complete (simulated)")
    
    return jsonify({
        "code": code,
        "status": transfer.status,
        "files": transfer.files,
        "progress": transfer.progress
    })

def start_croc_receive(transfer, code):
    """Start Croc receive process"""
    try:
        transfer.add_log("Starting Croc receiver...")
        
        # Create receive directory
        recv_dir = os.path.join(UPLOAD_DIR, f"{code}_received")
        os.makedirs(recv_dir, exist_ok=True)
        
        # croc --code <code>
        cmd = [CROC_BIN, "--code", code]
        
        transfer.add_log(f"Croc receiver: {' '.join(cmd)}")
        
        # Run croc receive (chdir to receive directory)
        process = subprocess.Popen(
            cmd,
            cwd=recv_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        transfer.croc_process = process
        
        # Read output
        for line in process.stdout:
            line = line.strip()
            if line:
                transfer.add_log(line)
                if "Receiving" in line or "received" in line.lower():
                    transfer.progress = 75
        
        # Wait for process
        process.wait()
        
        if process.returncode == 0:
            # List received files
            received_files = os.listdir(recv_dir)
            transfer.files.extend(received_files)
            transfer.progress = 100
            transfer.status = "complete"
            transfer.add_log(f"✓ Received {len(received_files)} file(s)")
        else:
            error = process.stderr.read()
            transfer.add_log(f"❌ Croc error: {error}")
            transfer.status = "error"
    
    except Exception as e:
        transfer.add_log(f"❌ Error starting Croc receive: {str(e)}")
        transfer.status = "error"

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
    print(f"📍 API: http://localhost:5000")
    print(f"🔗 Croc: {'✓ Available' if CROC_BIN else '✗ Not installed'}")
    print("🔗 Transfer endpoint: /api/send")
    app.run(debug=False, host='0.0.0.0', port=5000)
