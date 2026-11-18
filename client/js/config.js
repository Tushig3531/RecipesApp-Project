window.API_BASE = ["localhost", "127.0.0.1"].includes(location.hostname)
  ? `http://${location.hostname}:8080`
  : "https://recipes-flask-backend-521138187713.us-central1.run.app";