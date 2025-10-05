from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from cryptography.fernet import Fernet, InvalidToken
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")

def encrypt_bytes(b: bytes):
    key = Fernet.generate_key()
    f = Fernet(key)
    return key, f.encrypt(b)

def decrypt_bytes(b: bytes, key_str: str):
    try:
        f = Fernet(key_str.encode("utf-8"))
        return True, f.decrypt(b), None
    except InvalidToken:
        return False, None, "Invalid key or corrupted file."
    except Exception as e:
        return False, None, str(e)

BLOBS = {}  # in-memory demo storage (resets on restart)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/encrypt", methods=["POST"])
def api_encrypt():
    file = request.files.get("file")
    if not file:
        return {"error":"No file uploaded"}, 400
    key, cipher = encrypt_bytes(file.read())
    name = f"{file.filename}.encrypted"
    BLOBS["enc"] = (BytesIO(cipher), name)
    return {"key": key.decode("utf-8"), "download": url_for("download_blob", kind="enc")}

@app.route("/api/decrypt", methods=["POST"])
def api_decrypt():
    file = request.files.get("file")
    key = request.form.get("key","")
    if not file or not key:
        return {"error":"File and key are required"}, 400
    ok, data, err = decrypt_bytes(file.read(), key)
    if not ok:
        return {"error": err or "Decryption failed"}, 400
    name = file.filename[:-10] if file.filename.endswith(".encrypted") else file.filename
    BLOBS["dec"] = (BytesIO(data), name)
    return {"download": url_for("download_blob", kind="dec")}

@app.route("/download/<kind>")
def download_blob(kind):
    blob = BLOBS.get(kind)
    if not blob:
        flash("Nothing to download yet.")
        return redirect(url_for("index"))
    mem, name = blob
    mem.seek(0)
    return send_file(mem, as_attachment=True, download_name=name)

if __name__ == "__main__":
    app.run(debug=True)
