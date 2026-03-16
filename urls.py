import requests
import os
from django.http import HttpResponse, JsonResponse
from django.urls import path
MARTA_URL = "http://developer.itsmarta.com/RealtimeTrainService/RestServiceNextTrain/GetRealtimeArrivals"
def get_trains(request):
    key = request.GET.get("key")
    if not key:
        return JsonResponse({"error": "no key"}, status=400)
    try:
        resp = requests.get(MARTA_URL, params={"apiKey": key}, timeout=10)
        if resp.status_code == 401 or resp.status_code == 403:
            return JsonResponse({"error": "bad key"}, status=401)
        data = resp.json()
        if isinstance(data, dict) and not isinstance(data, list):
            return JsonResponse({"error": "bad key"}, status=401)
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
def home(request):
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>MARTA Train Tracker</title>
<style>
  body { font-family: monospace; background: #fff; color: #000; padding: 2rem; max-width: 900px; margin: 0 auto; }
  h1 { font-size: 1.4rem; margin-bottom: 0.25rem; }
  #subtitle { font-size: 0.85rem; color: #555; margin-bottom: 2rem; }
  #prompt { max-width: 480px; }
  #prompt h2 { font-size: 1rem; margin-bottom: 1rem; }
  #prompt ol { padding-left: 1.2rem; line-height: 2; font-size: 0.9rem; }
  #prompt a { color: #000; }
  #key-row { display: flex; gap: 0.5rem; margin-top: 1.25rem; }
  #key-input { flex: 1; font-family: monospace; font-size: 0.9rem; padding: 0.4rem 0.6rem; border: 1px solid #000; outline: none; }
  #key-input:focus { outline: 2px solid #000; }
  button { font-family: monospace; font-size: 0.9rem; padding: 0.4rem 1rem; border: 1px solid #000; background: #000; color: #fff; cursor: pointer; }
  button:hover { background: #333; }
  #key-error { color: red; font-size: 0.8rem; margin-top: 0.5rem; display: none; }
  #tracker { display: none; }
  #tracker-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 1rem; }
  #last-updated { font-size: 0.75rem; color: #888; }
  #change-key { font-size: 0.75rem; color: #888; cursor: pointer; text-decoration: underline; background: none; border: none; font-family: monospace; padding: 0; }
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  th { text-align: left; border-bottom: 2px solid #000; padding: 0.3rem 0.5rem; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
  td { padding: 0.3rem 0.5rem; border-bottom: 1px solid #eee; }
  tr:hover td { background: #f9f9f9; }
  .line-gold { color: #b8860b; font-weight: bold; }
  .line-red { color: #cc0000; font-weight: bold; }
  .line-blue { color: #0000cc; font-weight: bold; }
  .line-green { color: #007700; font-weight: bold; }
  .status-arriving { color: green; }
  .status-boarding { color: orange; }
  .status-scheduled { color: #888; }
  #loading { font-size: 0.9rem; color: #555; margin-top: 1rem; }
</style>
</head>
<body>
<h1>MARTA Rail Tracker</h1>
<div id="subtitle">Live train positions across the Atlanta rail network</div>
<div id="prompt">
  <h2>Enter your MARTA API key to continue</h2>
  <ol>
    <li>Go to <a href="https://www.itsmarta.com/app-developer-resources.aspx" target="_blank">itsmarta.com/app-developer-resources.aspx</a></li>
    <li>Fill out the short form to get your API key emailed to you</li>
    <li>Paste it below — this stays in your browser, it never goes anywhere</li>
  </ol>
  <div id="key-row">
    <input id="key-input" type="text" placeholder="Paste your API key here — get your own, you won't steal mine" />
    <button onclick="submitKey()">Go</button>
  </div>
  <div id="key-error">That key didn't work. Double-check it and try again.</div>
</div>
<div id="tracker">
  <div id="tracker-header">
    <strong>Active Trains</strong>
    <div style="display:flex; gap:1rem; align-items:baseline;">
      <span id="last-updated"></span>
      <button id="change-key" onclick="changeKey()">change key</button>
    </div>
  </div>
  <div id="loading">Loading trains...</div>
  <table id="train-table" style="display:none">
    <thead>
      <tr>
        <th>Line</th>
        <th>Train</th>
        <th>Direction</th>
        <th>Current Station</th>
        <th>Next Station</th>
        <th>Status</th>
        <th>Wait</th>
      </tr>
    </thead>
    <tbody id="train-body"></tbody>
  </table>
</div>
<script>
  let key = localStorage.getItem("marta_key") || "";
  let interval = null;
  if (key) {
    showTracker();
    fetchTrains();
  }
  function submitKey() {
    key = document.getElementById("key-input").value.trim();
    if (!key) return;
    document.getElementById("key-error").style.display = "none";
    fetchTrains(true);
  }
  function changeKey() {
    clearInterval(interval);
    key = "";
    localStorage.removeItem("marta_key");
    document.getElementById("tracker").style.display = "none";
    document.getElementById("prompt").style.display = "block";
    document.getElementById("key-input").value = "";
    document.getElementById("train-body").innerHTML = "";
    document.getElementById("train-table").style.display = "none";
    document.getElementById("loading").style.display = "block";
  }
  function showTracker() {
    document.getElementById("prompt").style.display = "none";
    document.getElementById("tracker").style.display = "block";
  }
  async function fetchTrains(isFirstTry = false) {
    try {
      let resp = await fetch("/api/trains/?key=" + encodeURIComponent(key));
      let data = await resp.json();
      if (!resp.ok) {
        if (isFirstTry) {
          document.getElementById("key-error").style.display = "block";
        }
        return;
      }
      localStorage.setItem("marta_key", key);
      showTracker();
      renderTrains(data);
      if (!interval) {
        interval = setInterval(fetchTrains, 15000);
      }
    } catch (e) {
      console.error(e);
    }
  }
  function renderTrains(trains) {
    let body = document.getElementById("train-body");
    let table = document.getElementById("train-table");
    let loading = document.getElementById("loading");
    if (!trains || trains.length === 0) {
      loading.textContent = "No trains found. Try again shortly.";
      return;
    }
    loading.style.display = "none";
    table.style.display = "table";
    let sorted = trains.slice().sort((a, b) => {
      let lineOrder = ["GOLD", "RED", "BLUE", "GREEN"];
      return lineOrder.indexOf(a.LINE) - lineOrder.indexOf(b.LINE);
    });
    body.innerHTML = sorted.map(train => {
      let line = (train.LINE || "").toUpperCase();
      let lineClass = "line-" + line.toLowerCase();
      let current = train.STATION || "Unknown";
      let next = train.NEXT_ARR || "--";
      let direction = train.DIRECTION || "--";
      let status = train.WAITING_SECONDS != null ? train.WAITING_SECONDS : "--";
      let trainID = train.TRAIN_ID || "--";
      let dest = train.DESTINATION || "--";
      let waitText = "--";
      if (status !== "--") {
        let secs = parseInt(status);
        if (secs < 60) waitText = secs + "s";
        else waitText = Math.floor(secs / 60) + "m " + (secs % 60) + "s";
      }
      let statusLabel = (train.STATUS || "").toLowerCase();
      let statusClass = "status-scheduled";
      if (statusLabel === "arriving") statusClass = "status-arriving";
      else if (statusLabel === "boarding") statusClass = "status-boarding";
      return `<tr>
        <td class="${lineClass}">${line}</td>
        <td>${trainID}</td>
        <td>${direction}</td>
        <td>${current}</td>
        <td>${dest}</td>
        <td class="${statusClass}">${train.STATUS || "--"}</td>
        <td>${waitText}</td>
      </tr>`;
    }).join("");
    let now = new Date();
    document.getElementById("last-updated").textContent = "updated " + now.toLocaleTimeString();
  }
  document.getElementById("key-input").addEventListener("keydown", e => {
    if (e.key === "Enter") submitKey();
  });
</script>
</body>
</html>"""
    return HttpResponse(html)
urlpatterns = [
    path("", home),
    path("api/trains/", get_trains),
]
