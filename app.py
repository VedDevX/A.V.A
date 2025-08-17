# ===============================
# Import All Necessary Libraries
# ===============================
from flask import Flask, render_template, request, jsonify
# Flask -> main web framework to create server and handle routes
# render_template -> loads HTML files like 'index.html' for the frontend
# request -> handles data sent from frontend (like user messages)
# jsonify -> sends data back to frontend in JSON format

# ===============================
# Import our custom backend modules
# ===============================
from assistant.chatbot import get_response
# get_response() -> our chatbot function that processes user messages
# It includes both greeting handling and dictionary lookups

# ===============================
# Initialize Flask App
# ===============================
app = Flask(__name__)
# Creates a Flask application object
# __name__ tells Flask where to look for templates and static files

# ===============================
# ROUTES (URLs for our app)
# ===============================

# -------------------------------------------
# Homepage Route
# -------------------------------------------
@app.route("/")  
# The URL route "/" is the homepage
def home():
    # Loads the frontend UI (index.html) and sends it to the browser
    return render_template("index.html")

# -------------------------------------------
# Chatbot API Route
# -------------------------------------------
@app.route("/api/chat", methods=["POST"])
# This route is called when frontend sends a user message
# methods=["POST"] means this route only accepts POST requests (sending data)
def chat_api():
    # 1. Ensure the request is JSON
    # Frontend must send "Content-Type: application/json"
    if not request.is_json:
        # If not JSON, return an error with HTTP status 415 (Unsupported Media Type)
        return jsonify({"error": "Content-Type must be application/json"}), 415
    
    # 2. Parse incoming JSON safely
    # Example payload from frontend: {"message": "hello"}
    # get_json(silent=True) returns an empty dict if parsing fails
    payload = request.get_json(silent=True) or {}
    
    # 3. Extract the "message" field from JSON and remove extra spaces
    user_msg = (payload.get("message") or "").strip()
    
    # 4. Validate the message
    if not user_msg:
        # If user message is empty, return an error with HTTP status 400 (Bad Request)
        return jsonify({"error": "Field 'message' cannot be empty"}), 400
    
    try:
        # 5. Process the message using our chatbot logic
        # get_response() takes the user message and returns the chatbot reply
        reply = get_response(user_msg)
    except Exception:
        # If the chatbot logic crashes, return a safe error message
        return jsonify({"error": "Internal error while generating reply"}), 500
    
    # 6. Return the chatbot reply in JSON format
    # Example: {"reply": "Hello! How can I help you?"}
    return jsonify({"reply": reply})

# ===============================
# Run Flask App
# ===============================
if __name__ == "__main__":
    # debug=True enables:
    # - Auto-restart of the server when code changes
    # - Detailed error messages in the browser
    app.run(debug=True)
