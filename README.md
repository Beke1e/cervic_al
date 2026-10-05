# CerviScope

Flask interface for the Squeezed CNN cervical-image classification research model.

## Run locally

Set operator credentials and a persistent Flask session key in PowerShell before starting the app:

```powershell
$env:CERVISCOPE_USERNAME = "operator"
$env:CERVISCOPE_PASSWORD = "use-a-long-unique-password"
$env:CERVISCOPE_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
python app.py
```

Open `http://127.0.0.1:5000`. The analysis workspace requires the configured operator credentials. About and Contact pages are public. To enable the Contact form to prepare a message, set `CERVISCOPE_CONTACT_EMAIL` to the project address. The form opens a draft in the user's email application; it does not send email from the server.

The classifier artifact `model.hdf5` is not included in this repository because it exceeds GitHub's file-size limit. Place the model file in the project root before using image analysis.

Set `CERVISCOPE_HTTPS=1` when serving behind HTTPS so the session cookie is marked Secure. Keep the secret key and operator password out of source control. The development server is not intended for production; use a production WSGI server and HTTPS deployment.

All classifier output is for research and educational use only and is not a medical diagnosis.