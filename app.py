import os
from flask import Flask, request, jsonify, render_template_string
from google import genai

app = Flask(__name__)

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Bot by Jahnavi</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #101827;
            color: white;
            max-width: 650px;
            margin: 25px auto;
            padding: 15px;
        }
        h1 { text-align: center; color: #7dd3fc; }
        #chat {
            height: 55vh;
            overflow-y: auto;
            background: #1e293b;
            padding: 12px;
            border-radius: 12px;
        }
        .msg {
            padding: 10px;
            margin: 8px 0;
            border-radius: 8px;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
        }
        .user { background: #075985; }
        .bot { background: #334155; }
        .controls { display: flex; gap: 8px; margin-top: 12px; }
        input {
            flex: 1;
            min-width: 0;
            padding: 12px;
            border-radius: 8px;
            border: 0;
        }
        button {
            padding: 12px;
            border: 0;
            border-radius: 8px;
            background: #38bdf8;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h1>Bot by Jahnavi</h1>
    <p>Ask questions about studies, coding, and more.</p>
    <div id="chat"></div>
    <div class="controls">
        <input id="message" placeholder="Type your question...">
        <button onclick="sendMessage()">Send</button>
    </div>
    <script>
        const chat = document.getElementById("chat");
        const input = document.getElementById("message");
        let history = [];

        function addMessage(text, who) {
            const div = document.createElement("div");
            div.className = "msg " + who;
            div.textContent = text;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        async function sendMessage() {
            const message = input.value.trim();
            if (!message) return;

            input.value = "";
            addMessage("You: " + message, "user");
            const button = document.querySelector("button");
            button.disabled = true;

            try {
                const response = await fetch("/chat", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        message: message,
                        history: history
                    })
                });

                const data = await response.json();
                if (!response.ok) throw new Error(data.error || "Request failed");

                addMessage("Bot: " + data.reply, "bot");
                history.push(
                    {role: "user", content: message},
                    {role: "assistant", content: data.reply}
                );
            } catch (error) {
                addMessage("Error: " + error.message, "bot");
            } finally {
                button.disabled = false;
                input.focus();
            }
        }

        input.addEventListener("keydown", e => {
            if (e.key === "Enter") sendMessage();
        });
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    if not os.environ.get("GEMINI_API_KEY"):
        return jsonify({"error": "API key is not configured."}), 500

    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Please enter a question."}), 400

    contents = []
    for item in history[-12:]:
        if item.get("role") in ("user", "assistant"):
            contents.append({
                "role": "model" if item["role"] == "assistant" else "user",
                "parts": [{"text": str(item.get("content", ""))}]
            })

    contents.append({
        "role": "user",
        "parts": [{"text": message}]
    })

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=contents
        )
        return jsonify({"reply": response.text or "No answer received."})
    except Exception:
        app.logger.exception("Gemini request failed")
        return jsonify({
            "error": "The AI request failed. Please try again."
        }), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
