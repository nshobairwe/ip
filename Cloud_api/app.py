from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
ping_results = {}

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/ping', methods=['POST'])
def update_ping():
    global ping_results
    ping_results = request.json
    return jsonify({"status": "ok"})

@app.route('/dashboard', methods=['GET'])
def dashboard():
    return jsonify(ping_results)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
