# Blink — Secure P2P File Transfer

A **lightweight, secure, peer-to-peer file transfer application** built with Python + Flask backend and a modern web PWA frontend.

## 🚀 Features

✅ **P2P File Transfer** — Secure direct file exchange via Croc relay  
✅ **QR Code Support** — Generate QR codes for instant code sharing  
✅ **Real-time Progress** — Live transfer status and logs  
✅ **No Accounts** — Zero registration, anonymous transfers  
✅ **PWA Ready** — Install as native app on any device  
✅ **Lightweight** — Minimal Python dependencies  

## 📋 Requirements

- Python 3.9+
- Flask 3.0+
- qrcode library
- Pillow (for QR images)

## 🛠️ Installation

```bash
# Clone or download the repo
cd blink

# Install Python dependencies
pip install -r requirements.txt

# Run the backend
python app.py
```

The server will start at `http://localhost:5000`

## 📱 Usage

### Send Files

```bash
curl -X POST http://localhost:5000/api/send
```

Returns:
```json
{
  "code": "A7K2M9",
  "qr_code": "data:image/png;base64,...",
  "status": "waiting"
}
```

### Upload Files

```bash
curl -X POST http://localhost:5000/api/upload/A7K2M9 \
  -F "files=@file1.txt" \
  -F "files=@file2.pdf"
```

### Receive Files

```bash
curl -X POST http://localhost:5000/api/transfer/A7K2M9/receive
```

### Download Files

```bash
curl http://localhost:5000/api/transfer/A7K2M9/download
```

## 🏗️ Architecture

```
Blink/
├── app.py                 # Python Flask backend
├── requirements.txt       # Python dependencies
├── index.html            # PWA frontend
├── manifest.json         # PWA metadata
├── sw.js                 # Service Worker
└── README.md             # This file
```

### Backend API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/send` | Start a new transfer |
| POST | `/api/upload/<code>` | Upload files |
| GET | `/api/transfer/<code>/status` | Get transfer status |
| POST | `/api/transfer/<code>/receive` | Receiver connects |
| GET | `/api/transfer/<code>/download` | List files for download |
| GET | `/api/transfer/<code>/file/<name>` | Download specific file |
| POST | `/api/cleanup` | Clean old transfers |

## 🌐 Deployment

### Local Development

```bash
python app.py
# Open http://localhost:5000
```

### Docker

```bash
docker build -t blink .
docker run -p 5000:5000 blink
```

### Heroku

```bash
git push heroku main
```

### PythonAnywhere

1. Upload files to PythonAnywhere
2. Create a Flask web app
3. Point to `app.py`
4. Done!

## 🔒 Security

- **No server storage** — Files deleted after transfer
- **Short codes** — 6-character transfer codes
- **Public relay** — Uses Croc's public relay (croc.schollz.com)
- **CORS enabled** — Works with any frontend

## 📊 How It Works

```
Sender                    Relay Server              Receiver
  |                            |                       |
  |--- POST /api/send -------->|                       |
  |<-- Code + QR Code ---------|                       |
  |                            |                       |
  |--- POST /upload ----->     |                       |
  |<-- Files Ready -----       |                       |
  |                            |<-- GET /status -------|
  |                            |-- Transfer Ready --->|
  |                            |                       |
  |--- Transfer Begins ------->|<-- /receive ---------|
  |                            |-- Sending Files --->|
  |<-- Complete -----------    |-- Download -------->|
```

## 🛠️ Development

### Add New Features

Edit `app.py` and add new routes:

```python
@app.route('/api/new-feature', methods=['POST'])
def new_feature():
    return jsonify({"status": "ok"})
```

### Customize Frontend

Edit `index.html` to change the UI, colors, or add features.

## 📝 License

MIT — Free to use, modify, and distribute.

## 🤝 Contributing

Found a bug? Have a feature idea? Open an issue or submit a PR!

---

**Built for speed. Designed for simplicity. Ready to share.**
