import json
import queue
from flask import Flask, request, jsonify, Response
import os

app = Flask(__name__)

# Queue holding incoming scores from the Pi, waiting to be
# pushed to the leaderboard page via SSE
pending_scores = queue.Queue()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "speedswipe-leaderboard.html")
# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the leaderboard HTML page."""
    return open(os.path.join(BASE_DIR, "speedswipe-leaderboard.html"), encoding="utf-8").read()



@app.route("/score", methods=["POST"])
def receive_score():
    """
    The Pi POSTs here when a round finishes, sending:
    { "time": 4.321, "attempts": 2 }

    We push it straight into the SSE queue so the page
    receives it in real time and triggers the name modal.
    """
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
    """
    Server-Sent Events endpoint -- the leaderboard page connects here
    on load and listens for scores pushed in from the Pi.

    When a score arrives, the page receives it and calls:
      window.triggerRun(avgTime, attempts)
    which opens the name entry modal.

    A keepalive ping is sent every 30 seconds to prevent the
    browser from dropping the connection.
    """
    def event_stream():
        while True:
            try:
                score = pending_scores.get(timeout=30)
                yield f"data: {json.dumps(score)}\n\n"
            except queue.Empty:
                yield "data: ping\n\n"  # Keepalive

    return Response(event_stream(), mimetype="text/event-stream")



# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=== SpeedSwipe Leaderboard Server ===")
    print("Open http://localhost:5000 in your browser")
    print("Waiting for scores from the Pi...\n")
    # host="0.0.0.0" makes the server reachable from other devices
    # on the same network (i.e. the Pi), not just localhost
    app.run(host="0.0.0.0", port=5000, threaded=True)
