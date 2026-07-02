# app.py
import os
import sys
import threading
import asyncio
import logging
from flask import Flask, jsonify

# ---------- Flask App ----------
app = Flask(__name__)

# ---------- HOME PAGE (सरल और काम करने वाला) ----------
@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>⚡ THANOS BOT ⚡</title>
    <style>
        body {
            background: linear-gradient(135deg, #0a0a0a, #1a0a2e, #0a0a0a);
            color: #fff;
            font-family: 'Courier New', monospace;
            text-align: center;
            padding-top: 50px;
            min-height: 100vh;
        }
        .glow {
            color: #ffd700;
            font-size: 50px;
            text-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
        }
        .status {
            color: #00ff88;
            font-size: 18px;
            margin: 20px 0;
        }
        .status i {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        .ascii {
            color: #00ffff;
            font-size: 12px;
            white-space: pre;
        }
    </style>
</head>
<body>
    <pre class="ascii">
    ████████╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗ ███████╗
    ╚══██╔══╝██║  ██║██╔══██╗████╗  ██║██╔═══██╗██╔════╝
       ██║   ███████║███████║██╔██╗ ██║██║   ██║███████╗
       ██║   ██╔══██║██╔══██║██║╚██╗██║██║   ██║╚════██║
       ██║   ██║  ██║██║  ██║██║ ╚████║╚██████╔╝███████║
       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝
    </pre>
    <h1 class="glow">⚡ THANOS BOT ⚡</h1>
    <p class="status"><i>●</i> Status: <span style="color:#00ff88;">ONLINE</span></p>
    <p style="color:#666;">v3.0.0 • Auto Uploader</p>
    <p style="color:#444; font-size:12px; margin-top:50px;">Made with ❤️ • 2026</p>
</body>
</html>
    """, 200

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "bot"}), 200

@app.route('/status')
def status():
    return jsonify({"status": "alive", "bot": "Thanos"}), 200

# ---------- बोट को बैकग्राउंड में चलाना ----------
def run_bot():
    """main.py को चलाएँ"""
    try:
        logging.info("🚀 Starting bot...")
        # main.py के main() function को कॉल करें
        import main
        asyncio.run(main.main())
    except Exception as e:
        logging.error(f"❌ Bot error: {e}")
        # Render को restart करने के लिए exit
        sys.exit(1)

# ---------- MAIN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s"
    )
    
    # बोट को बैकग्राउंड थ्रेड में चलाएँ
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    logging.info(f"✅ Bot thread started. Flask server on port {port}")
    
    # Flask server चलाएँ
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
