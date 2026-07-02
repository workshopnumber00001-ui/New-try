# app.py - Render Web Service के लिए (Thanos Theme + Bot Main Thread)
import os
import sys
import asyncio
import threading
import logging
from flask import Flask, jsonify

# ---------- Flask App ----------
app = Flask(__name__)

# ---------- HOME PAGE (Thanos Theme - Complete) ----------
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
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a0a2e 40%, #0a0a0a 100%);
            color: #fff;
            font-family: 'Courier New', monospace;
            text-align: center;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 20px;
            overflow-x: hidden;
        }
        .glow {
            text-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
        }
        .ascii-art {
            font-size: 12px;
            color: #00ffff;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.2);
            transition: all 0.5s ease;
            white-space: pre;
            font-family: 'Courier New', monospace;
            line-height: 1.2;
            margin-bottom: 20px;
        }
        .ascii-art:hover {
            transform: scale(1.03);
            color: #ff0066;
            text-shadow: 0 0 20px rgba(255, 0, 102, 0.4);
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
            letter-spacing: 8px;
        }
        @keyframes goldShine {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        .status-badge {
            display: inline-block;
            background: rgba(0, 255, 136, 0.15);
            border: 1px solid #00ff88;
            padding: 8px 30px;
            border-radius: 50px;
            color: #00ff88;
            font-size: 16px;
            margin: 15px 0;
            animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.02); }
        }
        .status-badge i { margin-right: 8px; }
        
        .version {
            color: #555;
            font-size: 14px;
            letter-spacing: 3px;
            margin-bottom: 10px;
        }
        .features {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 12px;
            margin: 25px 0;
            max-width: 700px;
        }
        .feature-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 12px 22px;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            font-size: 14px;
        }
        .feature-card:hover {
            transform: translateY(-4px);
            border-color: #ffd700;
            box-shadow: 0 10px 30px rgba(255, 215, 0, 0.1);
        }
        .feature-card i { margin-right: 8px; color: #ffd700; }
        
        footer {
            margin-top: 35px;
            padding: 15px 0;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            width: 100%;
            max-width: 500px;
        }
        footer img {
            border-radius: 50%;
            width: 36px;
            height: 36px;
        }
        .footer-text {
            color: #444;
            font-size: 12px;
            margin-top: 8px;
        }
        .footer-text .highlight { color: #ffd700; }
        
        /* Disintegration Effect */
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
        
        @media (max-width: 768px) {
            .thanos-title { font-size: 40px; letter-spacing: 4px; }
            .ascii-art { font-size: 8px; }
            .feature-card { padding: 10px 16px; font-size: 12px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- ASCII ART -->
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

        <!-- Title with Vanish Effect -->
        <h1 id="thanosTitle" class="thanos-title">⚡ THANOS ⚡</h1>
        <p class="version">v3.0.0 • AUTO UPLOADER BOT</p>

        <!-- Status -->
        <div class="status-badge">
            <i class="fas fa-circle" style="color: #00ff88;"></i>
            Bot is ONLINE
        </div>

        <!-- Features -->
        <div class="features">
            <div class="feature-card"><i class="fas fa-cloud-download-alt"></i> Auto Fetch</div>
            <div class="feature-card"><i class="fas fa-clock"></i> Scheduler</div>
            <div class="feature-card"><i class="fas fa-video"></i> DRM Support</div>
            <div class="feature-card"><i class="fas fa-robot"></i> AI Powered</div>
        </div>

        <!-- Footer -->
        <footer>
            <center>
                <img src="https://files.catbox.moe/ui41xs.jpg" width="36" height="36">
                <span style="color: #666; margin: 0 8px;">Powered By</span>
                <span style="color: #ffd700; font-weight: bold;">THANOS</span>
                <img src="https://files.catbox.moe/ui41xs.jpg" width="36" height="36">
                <div class="footer-text">
                    © 2026 • Made with ❤️ • <span class="highlight">THANOS</span>
                </div>
            </center>
        </footer>
    </div>

    <script>
        // Thanos Disintegration Effect (Click on Title)
        const title = document.getElementById("thanosTitle");
        if (title) {
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
                }, 2500);
            });
        }
    </script>
</body>
</html>
    """, 200

# ---------- HEALTH CHECK ENDPOINTS ----------
@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "thanos-bot", "version": "3.0.0"}), 200

@app.route('/status')
def status():
    return jsonify({
        "status": "alive",
        "bot": "Thanos Auto Uploader",
        "version": "3.0.0"
    }), 200

# ---------- FLASK SERVER (बैकग्राउंड थ्रेड में) ----------
def run_flask():
    """Flask को बैकग्राउंड थ्रेड में चलाएँ (Render के लिए)"""
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ---------- MAIN ----------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    logging.info("🌐 Starting Flask server in background thread...")
    
    # Flask को बैकग्राउंड थ्रेड में शुरू करें
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info("✅ Flask server started in background")
    
    # ---- बोट को मुख्य थ्रेड में चलाएँ (सबसे जरूरी) ----
    logging.info("🚀 Starting Thanos Bot in main thread...")
    
    try:
        import main
        asyncio.run(main.main())
    except KeyboardInterrupt:
        logging.info("🛑 Bot stopped by user")
    except Exception as e:
        logging.error(f"❌ Bot crashed: {e}")
        sys.exit(1)
