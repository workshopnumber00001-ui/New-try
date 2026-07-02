# app.py - Render Web Service के लिए (Flask + Bot Threading)
import os
import sys
import asyncio
import threading
import logging
from flask import Flask, jsonify

# ---------- Flask App ----------
app = Flask(__name__)

# ---------- HOME PAGE (Thanos Theme) ----------
@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ THANOS BOT ⚡</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a0a2e 50%, #0a0a0a 100%);
            color: #fff;
            font-family: 'Courier New', monospace;
            text-align: center;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            margin: 0;
            padding: 20px;
        }
        .glow {
            color: #ffd700;
            font-size: 60px;
            font-weight: 900;
            text-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
            animation: glowPulse 3s ease-in-out infinite;
        }
        @keyframes glowPulse {
            0%, 100% { text-shadow: 0 0 30px rgba(255, 215, 0, 0.3); }
            50% { text-shadow: 0 0 60px rgba(255, 215, 0, 0.6); }
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
        .ascii-art {
            color: #00ffff;
            font-size: 12px;
            white-space: pre;
            font-family: 'Courier New', monospace;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.2);
            line-height: 1.2;
        }
        .version {
            color: #555;
            font-size: 14px;
            margin-top: 10px;
            letter-spacing: 2px;
        }
        .features {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 15px;
            margin: 30px 0;
            max-width: 600px;
        }
        .feature-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 12px 20px;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }
        .feature-card:hover {
            transform: translateY(-5px);
            border-color: #ffd700;
            box-shadow: 0 10px 30px rgba(255, 215, 0, 0.1);
        }
        .footer-text {
            color: #444;
            font-size: 12px;
            margin-top: 40px;
        }
        .bot-name {
            color: #ffd700;
            font-weight: bold;
        }
        @media (max-width: 768px) {
            .glow { font-size: 40px; }
            .ascii-art { font-size: 8px; }
        }
    </style>
</head>
<body>
    <pre class="ascii-art">
    ████████╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗ ███████╗
    ╚══██╔══╝██║  ██║██╔══██╗████╗  ██║██╔═══██╗██╔════╝
       ██║   ███████║███████║██╔██╗ ██║██║   ██║███████╗
       ██║   ██╔══██║██╔══██║██║╚██╗██║██║   ██║╚════██║
       ██║   ██║  ██║██║  ██║██║ ╚████║╚██████╔╝███████║
       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝
    </pre>
    
    <h1 class="glow">⚡ THANOS ⚡</h1>
    <p class="version">v3.0.0 • AUTO UPLOADER BOT</p>
    
    <div class="status">
        <i>●</i> Status: <span style="color:#00ff88;">ONLINE</span>
    </div>

    <div class="features">
        <div class="feature-card">📥 Auto Fetch</div>
        <div class="feature-card">⏰ Scheduler</div>
        <div class="feature-card">🎬 DRM Support</div>
        <div class="feature-card">⚡ Fast Upload</div>
    </div>

    <div class="footer-text">
        Made with ❤️ • <span class="bot-name">THANOS</span> • 2026
    </div>
</body>
</html>
    """, 200

# ---------- HEALTH CHECK ----------
@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "thanos-bot"}), 200

@app.route('/status')
def status():
    return jsonify({"status": "alive", "bot": "Thanos Auto Uploader", "version": "3.0.0"}), 200

# ---------- BOT LAUNCHER (BACKGROUND THREAD) ----------
def run_bot():
    """अलग थ्रेड में बोट चलाएँ"""
    try:
        # नया event loop बनाएँ (Render के लिए जरूरी)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # main.py import करें और main() चलाएँ
        import main
        loop.run_until_complete(main.main())
    except Exception as e:
        logging.error(f"❌ Bot crashed: {e}")
        sys.exit(1)

# ---------- MAIN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    
    # Logging setup
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    logging.info("🚀 Starting Thanos Bot in background thread...")
    
    # बोट को डेमॉन थ्रेड में शुरू करें
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    logging.info(f"✅ Bot thread started. Flask server running on port {port}")
    logging.info("🌐 Open your Render URL to see the Thanos page!")
    
    # Flask server चलाएँ
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
