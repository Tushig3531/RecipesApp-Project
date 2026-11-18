// Local testing uses the same hostname as the page so cookies work; production uses Render
window.API_BASE = ["localhost", "127.0.0.1"].includes(location.hostname)
  ? `http://${location.hostname}:8080`
  : "https://recipes-flask-backend-6pfm.onrender.com"\;
