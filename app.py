import base64
import hmac
import io
import os
import secrets
from functools import wraps
from urllib.parse import quote, urlencode

from flask import Flask, abort, redirect, render_template, request, session, url_for


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["SECRET_KEY"] = os.environ.get("CERVISCOPE_SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("CERVISCOPE_HTTPS") == "1"
app.config["OPERATOR_USERNAME"] = os.environ.get("CERVISCOPE_USERNAME", "")
app.config["OPERATOR_PASSWORD"] = os.environ.get("CERVISCOPE_PASSWORD", "")
app.config["CONTACT_EMAIL"] = os.environ.get("CERVISCOPE_CONTACT_EMAIL", "")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.hdf5")
class_names = ["Negative", "Positive", "Suspicious"]
allowed_extensions = {"jpg", "jpeg", "png", "jfif"}
model = None


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


@app.before_request
def protect_post_requests():
    session.setdefault("csrf_token", secrets.token_urlsafe(32))
    if request.method == "POST":
        submitted_token = request.form.get("csrf_token", "")
        if not hmac.compare_digest(submitted_token, session["csrf_token"]):
            abort(400)


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


@app.context_processor
def inject_template_values():
    return {"csrf_token": session.get("csrf_token", "")}


def load_classifier():
    global model

    if model is None:
        from tensorflow.keras.models import load_model

        model = load_model(MODEL_PATH)

    return model


def predict(image_bytes):
    from tensorflow.keras.preprocessing.image import img_to_array, load_img

    image = load_img(io.BytesIO(image_bytes), target_size=(64, 64), color_mode="rgb")
    image_array = img_to_array(image).astype("float32") / 255.0
    result = load_classifier().predict(image_array.reshape(1, 64, 64, 3), verbose=0)
    probabilities = result[0].reshape(-1)

    if len(probabilities) != len(class_names):
        raise ValueError("Model output does not match the configured class names.")

    ranked = sorted(
        zip(class_names, probabilities),
        key=lambda prediction: float(prediction[1]),
        reverse=True,
    )
    return [
        {"name": name, "probability": round(float(probability) * 100, 2)}
        for name, probability in ranked
    ]


@app.route("/")
@login_required
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    credentials_configured = bool(
        app.config["OPERATOR_USERNAME"] and app.config["OPERATOR_PASSWORD"]
    )

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        expected_username = app.config["OPERATOR_USERNAME"]
        expected_password = app.config["OPERATOR_PASSWORD"]

        if not credentials_configured:
            error = "Sign-in is not configured. Ask the system administrator to enable operator credentials."
        elif hmac.compare_digest(username, expected_username) and hmac.compare_digest(
            password, expected_password
        ):
            session.clear()
            session["authenticated"] = True
            session["username"] = expected_username
            session["csrf_token"] = secrets.token_urlsafe(32)
            return redirect(url_for("home"))
        else:
            error = "The username or password is incorrect."

    return render_template(
        "login.html",
        error=error,
        credentials_configured=credentials_configured,
    )


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if not name or not email or not message:
            error = "Complete each field before preparing your message."
        elif len(name) > 120 or len(email) > 254 or len(message) > 5000:
            error = "Some information is too long. Please shorten your message and try again."
        elif not app.config["CONTACT_EMAIL"]:
            error = "A project contact address has not been configured, so no message was sent."
        else:
            subject = f"CerviScope inquiry from {name}"
            body = f"Name: {name}\nReply-to: {email}\n\n{message}"
            mailto = f"mailto:{quote(app.config['CONTACT_EMAIL'], safe='@.+-_')}?{urlencode({'subject': subject, 'body': body})}"
            return redirect(mailto)

    return render_template("contact.html", error=error)


@app.route("/success", methods=["GET", "POST"])
@login_required
def success():
    if request.method == "GET":
        return redirect(url_for("home"))

    uploaded_file = request.files.get("file")
    if not uploaded_file or not uploaded_file.filename:
        return render_template("index.html", error="Choose an image to analyze."), 400

    if not allowed_file(uploaded_file.filename):
        return render_template(
            "index.html",
            error="Use a JPG, JPEG, PNG, or JFIF image.",
        ), 400

    image_bytes = uploaded_file.read()
    if not image_bytes:
        return render_template("index.html", error="The selected image is empty."), 400

    try:
        predictions = predict(image_bytes)
    except Exception:
        app.logger.exception("Image prediction failed")
        return render_template(
            "index.html",
            error="The image could not be analyzed. Check the image and model setup, then try again.",
        ), 500

    extension = uploaded_file.filename.rsplit(".", 1)[1].lower()
    mime_type = "image/jpeg" if extension in {"jpg", "jpeg", "jfif"} else "image/png"
    image_data = base64.b64encode(image_bytes).decode("ascii")
    return render_template(
        "success.html",
        image_data=f"data:{mime_type};base64,{image_data}",
        predictions=predictions,
    )


@app.errorhandler(413)
def too_large(_error):
    if session.get("authenticated"):
        return render_template(
            "index.html",
            error="Image is too large. Choose a file smaller than 16 MB.",
        ), 413
    return render_template("login.html", error="Request is too large."), 413


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")