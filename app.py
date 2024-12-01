from flask import Flask, render_template, request, redirect, url_for, session
from transformers import MarianMTModel, MarianTokenizer
from huggingface_hub import login
from langdetect import detect, LangDetectException

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Secret key for session management

# In-memory storage for users and messages
users = {"user1": "password1", "user2": "password2"}
messages = []

# Set Hugging Face token using environment variable (or hardcoded if needed)
hf_token = "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"  # Your Hugging Face token

if hf_token:
    login(token=hf_token)
else:
    print("Hugging Face token not found.")

# Initialize models without Telugu-specific handling
def get_translation_model(source_lang, target_lang):
    model_name = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"
    
    # Load model and tokenizer with Hugging Face token
    model = MarianMTModel.from_pretrained(model_name, use_auth_token=hf_token)
    tokenizer = MarianTokenizer.from_pretrained(model_name, use_auth_token=hf_token)
    
    return model, tokenizer

# Route for user login (GET and POST methods)
@app.route("/", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        target_language = request.form["target_language"]

        # Validate user credentials
        if users.get(username) == password:
            session["username"] = username  # Store the logged-in user's username in session
            session["target_language"] = target_language  # Store the selected target language
            return redirect(url_for("chat"))  # Redirect to chat after login
        else:
            return "Invalid username or password. Please try again."

    return render_template("login.html")

# Route for chat functionality (GET and POST methods)
@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "username" not in session:
        return redirect(url_for("login_page"))  # Redirect to login if not logged in

    username = session["username"]
    target_language = session["target_language"]  # Get target language from session
    other_user = "user1" if username == "user2" else "user2"

    if request.method == "POST":
        message = request.form["message"]
        if message:
            # Detect the language of the typed message
            source_lang = detect_language(message)
            
            # If the detected language matches the target language, don't show warning
            if source_lang != target_language:
                # Show warning only when the source language is different from the target language
                warning_message = f"Warning: The message is in {source_lang}, not in {target_language}. It may be translated incorrectly."
                return render_template("chat.html", warning_message=warning_message)

            messages.append({
                "sender": username,
                "receiver": other_user,
                "text": message,
                "sender_lang": target_language
            })
            return redirect(url_for("chat"))

    # Translate messages for the current user
    user_messages = []
    for msg in messages:
        if msg["receiver"] == username or msg["sender"] == username:
            if msg["sender"] == username:  # Sender's message is in their selected language
                user_messages.append(f"{msg['sender']}: {msg['text']}")
            else:  # Incoming message needs to be translated into the user's target language
                source_lang = msg["sender_lang"]
                model, tokenizer = get_translation_model(source_lang, target_language)
                translated_text = translate_message(msg["text"], model, tokenizer)
                user_messages.append(f"{msg['sender']}: {translated_text}")

    return render_template(
        "chat.html", username=username, other_user=other_user, chat_history=user_messages, warning_message=None
    )

# Function to detect the language of a message
def detect_language(message):
    try:
        detected_language = detect(message)
        # Map langdetect language codes to the appropriate model language codes
        lang_mapping = {
            "en": "en",
            "hi": "hi"
        }
        return lang_mapping.get(detected_language, "en")  # Default to 'en' if detection fails
    except LangDetectException:
        return "en"  # Default to 'en' if language detection fails

# Function to handle translation using MarianMT model
def translate_message(message, model, tokenizer):
    inputs = tokenizer(message, return_tensors="pt", padding=True, truncation=True)
    translated = model.generate(**inputs)
    translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
    return translated_text

# Route for logging out
@app.route("/logout")
def logout():
    session.pop("username", None)  # Remove the username from the session to log out
    session.pop("target_language", None)  # Remove the target language from session
    return redirect(url_for("login_page"))  # Redirect to login page after logging out

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

 # Run the app with debug mode on
