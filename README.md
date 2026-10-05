# CerviScope

CerviScope is a Flask web interface for exploring a Squeezed Convolutional Neural Network (CNN) that classifies cervical images. It provides an operator sign-in, an image-analysis workspace, public project information, and a contact form that prepares an email draft.

> **Research use only.** CerviScope is a technical and educational research interface, not a medical device. Its predictions are not diagnoses, screening results, or treatment recommendations. Have images and any model output reviewed by a qualified clinician. Only upload images that you are authorized to use, and do not include patient-identifying or other sensitive health information.

## Features

- Operator sign-in protects access to the image-analysis workspace.
- Accepts JPG, JPEG, PNG, and JFIF images up to 16 MB.
- Resizes images to 64 × 64 RGB and scales pixel values before inference.
- Displays model scores for three configured classes: **Negative**, **Positive**, and **Suspicious**.
- Includes public About and Contact pages.
- Processes uploaded image bytes in memory; this interface does not save them to an upload directory. Hosting infrastructure and server logs may have their own retention policies.

## Requirements

- Python with `pip`
- The dependencies listed in [`requirements.txt`](requirements.txt) (currently TensorFlow 2.17.x)
- The trained model file `model.hdf5` for image analysis

## Setup

Clone the repository and move into the project directory:

```bash
git clone https://github.com/Beke1e/cervic_al.git
cd cervic_al
```

Create and activate a virtual environment.

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the Python dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Model file

The trained `model.hdf5` file is not included in this repository because it is larger than GitHub's standard file-size limit. Obtain the correct model from the project maintainer or another trusted source, then place it in the project root alongside `app.py`:

```text
cervic_al/
├── app.py
├── model.hdf5
├── requirements.txt
├── static/
└── templates/
```

The file is excluded from Git by `.gitignore`, so it stays on your machine and is not included in ordinary commits or pushes. Without it, the website can start, but image analysis will fail. Use only a trusted model that is compatible with this project; predictions depend on the model file.

## Configuration and startup

Set operator credentials and a persistent Flask secret key in the environment before starting the application. Do not use example credentials or commit real credentials or secret keys to source control.

**Windows PowerShell**

```powershell
$env:CERVISCOPE_USERNAME = "operator"
$env:CERVISCOPE_PASSWORD = "replace-with-a-strong-password"
$env:CERVISCOPE_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
python app.py
```

**macOS / Linux**

```bash
export CERVISCOPE_USERNAME="operator"
export CERVISCOPE_PASSWORD="replace-with-a-strong-password"
export CERVISCOPE_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python app.py
```

Open <http://127.0.0.1:5000> in your browser and sign in with the configured operator credentials. If credentials are not configured, sign-in is disabled.

The secret key in these examples is generated for the current shell session. For a persistent deployment, configure a securely generated secret through your hosting environment and keep it unchanged across application restarts so existing sessions remain valid.

### Optional settings

| Variable | Purpose |
| --- | --- |
| `CERVISCOPE_USERNAME` | Operator sign-in username. |
| `CERVISCOPE_PASSWORD` | Operator sign-in password. |
| `CERVISCOPE_SECRET_KEY` | Persistent secret used to sign Flask sessions. |
| `CERVISCOPE_CONTACT_EMAIL` | Recipient address used to prepare a contact email draft. The form does not send email itself. |
| `CERVISCOPE_HTTPS` | Set to `1` when served behind HTTPS to mark the session cookie as Secure. |
| `FLASK_DEBUG` | Set to `1` to enable Flask debug mode for local development only. Never enable debug mode in production. |

## Contact form

Set `CERVISCOPE_CONTACT_EMAIL` to enable the Contact form. Submitting the form opens a pre-filled draft in the visitor's default email application; the server does not send the message. Do not put sensitive health information in a contact message.

## Project layout

```text
app.py                 Flask routes, authentication, and image inference
requirements.txt       Python dependency list
static/css/app.css     Application styles
templates/             Jinja templates for application pages
model.hdf5             Locally supplied trained model (not tracked by Git)
```

## Deployment notes

The built-in Flask development server is intended for local development, not public production hosting. For deployment, use a production WSGI server, HTTPS, strong unique operator credentials, and a securely managed persistent `CERVISCOPE_SECRET_KEY`. Configure `CERVISCOPE_HTTPS=1` when TLS is terminated by a trusted HTTPS proxy. Review the hosting platform's file-size limits, privacy practices, and logging/retention settings before using any real images.

## Attribution

Powered by #Bekele Mulat • University of Gondar • [+251-936 328 953](tel:+251936328953) • [bekemuler3@gmail.com](mailto:bekemuler3@gmail.com)
