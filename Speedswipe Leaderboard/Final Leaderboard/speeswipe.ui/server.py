import json
import queue
import os
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

pending_scores = queue.Queue()

HTML_PATH = r"C:\Users\gauta\Documents\Speedswipe Leaderboard\speeswipe_ui\speedswipe-leaderboard.html"

@app.route("/")
def index():
    return open(HTML_PATH, encoding="utf-8").read()

@app.route("/score", methods=["POST"])
def receive_score():
    data = request.json
    elapsed  = data.get("time")
    attempts = data.get("attempts", 1)
    if elapsed is None:
        return jsonify({"error": "No time provided"}), 400
    print(f"[Pi] New score: {elapsed:.3f}s over {attempts} attempt(s)")
    pending_scores.put({"time": elapsed, "attempts": attempts})
    return jsonify({"status": "received"})

@app.route("/stream")
def stream():
    def event_stream():
        while True:
            try:
                score = pending_scores.get(timeout=30)
                yield f"data: {json.dumps(score)}\n\n"
            except queue.Empty:
                yield "data: ping\n\n"
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == "__main__":
    print("=== SpeedSwipe Leaderboard Server ===")
    print("Open http://localhost:5000 in your browser")
    app.run(host="0.0.0.0", port=5000, threaded=True)