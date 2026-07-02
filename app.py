# app.py
import os
import sys
import threading
import asyncio
import logging
from flask import Flask, jsonify

# ---------- मुख्य बोट मॉड्यूल (main.py) ----------
try:
    import main
except ImportError as e:
    logging.error(f"❌ main.py import failed: {e}")
    sys.exit(1)

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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
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
            overflow-x: hidden;
        }
        .glow {
            text-shadow: 0 0 20px rgba(255, 215, 0, 0.3), 0 0 40px rgba(255, 215, 0, 0.1);
        }
        .ascii-art {
            font-size: 12px;
            color: #00ffff;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
            transition: all 0.5s ease;
            line-height: 1.2;
            white-space: pre;
            font-family: 'Courier New', monospace;
        }
        .ascii-art:hover {
            transform: scale(1.05);
            color: #ff0066;
            text-shadow: 0 0 20px rgba(255, 0, 102, 0.5);
        }
        .thanos-title {
            font-size: 60px;
            font-weight: 900;
            background: linear-gradient(135deg, #ffd700, #ff6b00, #ffd700);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-size: 200% 200%;
            animation: goldShine 3s ease-in-out infinite;
            cursor: pointer;
            display: inline-block;
            margin: 20px 0;
            letter-spacing: 8px;
            text-shadow: none;
        }
        @keyframes goldShine {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        .status-badge {
            display: inline-block;
            background: rgba(0, 255, 136, 0.15);
            border: 1px solid #00ff88;
            padding: 8px 25px;
            border-radius: 50px;
            color: #00ff88;
            font-size: 16px;
            margin: 10px 0;
            animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.02); }
        }
        .status-badge i {
            margin-right: 8px;
        }
        .features {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 15px;
            margin: 30px 0;
            max-width: 800px;
        }
        .feature-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 15px 25px;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            flex: 1;
            min-width: 150px;
        }
        .feature-card:hover {
            transform: translateY(-5px);
            border-color: #ffd700;
            box-shadow: 0 10px 30px rgba(255, 215, 0, 0.1);
        }
        .feature-card i {
            font-size: 28px;
            color: #ffd700;
            display: block;
            margin-bottom: 8px;
        }
        .feature-card span {
            font-size: 13px;
            color: #aaa;
        }
        footer {
            margin-top: 40px;
            padding: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            width: 100%;
            max-width: 600px;
        }
        footer img {
            border-radius: 50%;
            width: 40px;
            height: 40px;
        }
        .footer-text {
            color: #666;
            font-size: 12px;
            margin-top: 10px;
        }
        /* Disintegration effect */
        @keyframes vanish {
            0% { opacity: 1; transform: translate(0,0) scale(1) rotate(0deg); }
            30% { opacity: 0.8; transform: translate(10px,-15px) scale(1.1) rotate(10deg); }
            70% { opacity: 0.3; transform: translate(-20px,25px) scale(0.8) rotate(-20deg); }
            100% { opacity: 0; transform: translate(-40px,50px) scale(0.3) rotate(-45deg); }
        }
        .disintegrate span {
            display: inline-block;
            animation: vanish 1.2s forwards;
        }
        .version {
            color: #555;
            font-size: 14px;
            letter-spacing: 2px;
        }
        @media (max-width: 768px) {
            .thanos-title { font-size: 40px; letter-spacing: 4px; }
            .ascii-art { font-size: 8px; }
            .feature-card { min-width: 120px; padding: 12px 18px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <pre class="ascii-art">
╔══════════════════════════════════════════════════════════════╗
║   ████████╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗ ███████╗    ║
║   ╚══██╔══╝██║  ██║██╔══██╗████╗  ██║██╔═══██╗██╔════╝    ║
║      ██║   ███████║███████║██╔██╗ ██║██║   ██║███████╗    ║
║      ██║   ██╔══██║██╔══██║██║╚██╗██║██║   ██║╚════██║    ║
║      ██║   ██║  ██║██║  ██║██║ ╚████║╚██████╔╝███████║    ║
║      ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝    ║
╚══════════════════════════════════════════════════════════════╝
        </pre>

        <h1 id="thanosTitle" class="thanos-title">⚡ THANOS ⚡</h1>
        <p class="version">v3.0.0 • AUTO UPLOADER BOT</p>

        <div class="status-badge">
            <i class="fas fa-circle" style="color: #00ff88;"></i>
            Bot is ONLINE
        </div>

        <div class="features">
            <div class="feature-card">
                <i class="fas fa-cloud-download-alt"></i>
                <span>Auto Fetch</span>
            </div>
            <div class="feature-card">
                <i class="fas fa-clock"></i>
                <span>Scheduler</span>
            </div>
            <div class="feature-card">
                <i class="fas fa-video"></i>
                <span>DRM Support</span>
            </div>
            <div class="feature-card">
                <i class="fas fa-robot"></i>
                <span>AI Powered</span>
            </div>
        </div>

        <footer>
            <center>
                <img src="https://files.catbox.moe/ui41xs.jpg" width="40" height="40">
                <span style="color: #888; margin: 0 10px;">Powered By</span>
                <span style="color: #ffd700; font-weight: bold;">THANOS</span>
                <img src="https://files.catbox.moe/ui41xs.jpg" width="40" height="40">
                <div class="footer-text">
                    © 2026 • Auto Uploader • Made with ❤️
                </div>
            </center>
        </footer>
    </div>

    <script>
        // Thanos Disintegration Effect
        const title = document.getElementById("thanosTitle");
        title.addEventListener("click", function() {
            const text = this.innerText;
            this.innerHTML = "";
            text.split("").forEach((char, i) => {
                const span = document.createElement("span");
                span.textContent = char === " " ? "\u00A0" : char;
                span.style.animationDelay = (i * 0.08) + "s";
                span.classList.add("disintegrate");
                this.appendChild(span);
            });
            // Reset after animation
            setTimeout(() => {
                this.innerHTML = "⚡ THANOS ⚡";
            }, 2000);
        });
    </script>
</body>
</html>
    """, 200

# ---------- HEALTH CHECK ENDPOINTS ----------
@app.route('/health')
def health():
    return jsonify({"status": "alive", "service": "telegram-bot", "version": "3.0.0"}), 200

@app.route('/status')
def status():
    return jsonify({
        "status": "ok",
        "uptime": "running",
        "bot": "Thanos Auto Uploader",
        "version": "3.0.0"
    }), 200

# ---------- BOT LAUNCHER (बैकग्राउंड थ्रेड) ----------
def run_bot():
    """main.py के main() async function को चलाएँ"""
    try:
        logging.info("🚀 Starting Telegram bot in background thread...")
        asyncio.run(main.main())
    except Exception as e:
        logging.error(f"❌ Bot crashed: {e}")
        sys.exit(1)

# ---------- MAIN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    logging.info("🌐 Starting Flask server for Render...")
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logging.info(f"✅ Bot thread started. Flask running on port {port}")
    
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
