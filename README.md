# Blink — Secure P2P File Transfer

A **lightweight, secure, peer-to-peer file transfer application** built with Python + Flask backend (with real Croc integration) and a modern web PWA frontend.

## 🚀 Features

✅ **Real P2P File Transfer** — Actual Croc-powered secure direct file exchange  
✅ **QR Code Support** — Generate QR codes for instant code sharing  
✅ **Real-time Progress** — Live transfer status and logs  
✅ **No Accounts** — Zero registration, anonymous transfers  
✅ **PWA Ready** — Install as native app on any device  
✅ **Lightweight** — Minimal Python dependencies  
✅ **Croc Integration** — Uses real Croc binary for transfers  

## 📋 Requirements

- Python 3.9+
- Flask 3.0+
- qrcode library
- Pillow (for QR images)
- **Croc** (for real transfers) — `brew install croc` or `apt install croc`

## 🛠️ Installation

```bash
# Clone or download the repo
cd blink

# Install Python dependencies
pip install -r requirements.txt

# Install Croc (if you want real transfers)
# macOS:
brew install croc

# Linux:
sudo apt install croc

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
├── app.py                 # Python Flask backend + Croc integration
├── requirements.txt       # Python dependencies
├── index.html            # PWA frontend
├── manifest.json         # PWA metadata
├── sw.js                 # Service Worker
├── Dockerfile            # Container config
├── Procfile              # Railway deployment
└── README.md             # This file
```

### Backend API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check + Croc status |
| POST | `/api/send` | Start a new transfer |
| POST | `/api/upload/<code>` | Upload files |
| GET | `/api/transfer/<code>/status` | Get transfer status |
| POST | `/api/transfer/<code>/receive` | Receiver connects |
| GET | `/api/transfer/<code>/download` | List files for download |
| GET | `/api/transfer/<code>/file/<name>` | Download specific file |
| POST | `/api/cleanup` | Clean old transfers |

## 🔄 How Croc Integration Works

**Blink uses Croc for real P2P transfers:**

```
Sender                    Croc Relay               Receiver
  |                            |                       |
  |-- POST /api/send -------->|                       |
  |<-- Code + QR Code ---------|                       |
  |                            |                       |
  |-- POST /upload ----->      |                       |
  |<-- Files Ready -----       |                       |
  |                            |                       |
  |-- croc send --code A7K2M9-->|                       |
  |                            |<-- POST /receive -------|
  |                            |-- croc --code A7K2M9 ->|
  |<-- Croc Transfer Begins ---|-- Receiving Files -->|
  |-- Files Streaming -------->|-- Streaming ---------->|
  |<-- Complete -----------    |<-- Complete ----------|
```

**When Croc is unavailable,** Blink falls back to file storage simulation.

## 🌐 Deployment

### Local Development

```bash
python app.py
# Open http://localhost:5000
```

### Railway (Recommended for Production)

1. Push to GitHub
2. Go to https://railway.app
3. Connect your repo → Deploy
4. Railway auto-detects Python and runs `gunicorn app:app`
5. Your backend is live at `https://blink-app-production-cf8b.up.railway.app`

### Docker

```bash
docker build -t blink .
docker run -p 5000:5000 blink
```

### Vercel (Frontend PWA only)

1. Deploy `index.html` to Vercel
2. Update `API_BASE` in `index.html` to your backend URL
3. PWA will call real backend

## 🔒 Security

- **No server storage** — Files deleted after transfer (Croc handles P2P)
- **Short codes** — 6-character transfer codes
- **Public relay** — Uses Croc's public relay (croc.schollz.com)
- **CORS enabled** — Works with any frontend
- **Peer-to-peer** — Direct file exchange, no middle-man

## 📊 Real Transfer Flow

1. **Sender** uploads file → Backend stores temporarily
2. **Backend** starts `croc send --code A7K2M9 file.txt`
3. **Croc relay** registers sender with code
4. **Receiver** calls `/api/transfer/A7K2M9/receive`
5. **Backend** starts `croc --code A7K2M9` in receive dir
6. **Croc P2P** connects sender & receiver directly
7. **Files transfer** peer-to-peer (relay only tunnels if needed)
8. **Cleanup** removes temporary files after transfer

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

### Test Croc Integration

Check if Croc is installed:
```bash
croc --version
```

Monitor transfers in real-time:
```bash
curl http://localhost:5000/api/transfer/YOURCODE/status
```

## 📝 License

MIT — Free to use, modify, and distribute.

## 🤝 Contributing

Found a bug? Have a feature idea? Open an issue or submit a PR!

---

**Built for speed. Designed for simplicity. Powered by Croc. Ready to share.**
