import subprocess
import concurrent.futures
import threading
import time
import requests

# Cloud endpoint to receive ping results
cloud_url = "https://ip-9c2q.onrender.com"  # Adjust if your endpoint differs
ping_interval = 5  # seconds between ping rounds

# Define regions with WAN, Gateway, and LAN IPs
regions = {
    "Dar es Salaam": {"wan": "10.8.235.22", "gateway": "10.8.235.21", "lan": ["10.11.0.0", "10.11.0.1", "10.11.0.2"]},
    "Temeke": {"wan": "10.8.238.250", "gateway": "10.8.238.249", "lan": ["10.8.63.0", "10.8.63.1", "10.8.63.3"]},
    "Kinondoni": {"wan": "10.8.234.6", "gateway": "10.8.234.5", "lan": ["10.12.2.0", "10.12.2.1", "10.12.2.3"]},
    "Upanga": {"wan": "10.8.238.226", "gateway": "10.8.238.225", "lan": ["10.12.3.0", "10.12.3.1", "10.12.3.3"]},
    "Ilala": {"wan": "10.8.234.2", "gateway": "10.8.234.1", "lan": ["10.12.6.0", "10.12.6.1", "10.12.6.3"]},
    "Dodoma": {"wan": "10.20.251.82", "gateway": "10.20.251.81", "lan": ["10.20.11.0", "10.20.11.1", "10.20.11.3"]},
    "Tabora": {"wan": "10.20.251.206", "gateway": "10.20.251.205", "lan": ["10.20.12.0", "10.20.12.1", "10.20.12.3"]},
    "Shinyanga": {"wan": "10.20.251.226", "gateway": "10.20.251.225", "lan": ["10.20.13.0", "10.20.13.1", "10.20.13.3"]},
    "Mwanza": {"wan": "10.20.254.226", "gateway": "10.20.254.225", "lan": ["10.20.63.0", "10.20.63.1", "10.20.63.3"]},
    "Iringa": {"wan": "10.20.251.42", "gateway": "10.20.251.41", "lan": ["10.24.75.0", "10.24.75.1", "10.24.75.3"]},
    "Kigoma": {"wan": "10.20.252.66", "gateway": "10.20.252.65", "lan": ["10.4.0.0", "10.4.0.1", "10.4.0.2"]},
    "Kagera": {"wan": "10.20.252.70", "gateway": "10.20.252.69", "lan": ["10.4.1.0", "10.4.1.1", "10.4.1.3"]},
    "Musoma": {"wan": "10.20.252.70", "gateway": "10.20.252.73", "lan": ["10.4.2.0", "10.4.2.1", "10.4.2.3"]},
    "Singida": {"wan": "10.8.234.6", "gateway": "10.20.248.17", "lan": ["10.4.3.0", "10.4.3.1", "10.4.3.3"]},
    "Lindi": {"wan": "10.8.238.66", "gateway": "10.8.238.70", "lan": ["10.4.4.0", "10.4.4.1", "10.4.4.3"]},
    "Mtwara": {"wan": "10.8.238.70", "gateway": "10.20.252.69", "lan": ["10.4.5.0", "10.4.5.1", "10.4.5.3"]},
    "Metropolitan": {"wan": "10.8.235.142", "gateway": "10.8.235.141", "lan": ["10.4.6.0", "10.4.6.1", "10.4.6.3"]},
    "Arusha": {"wan": "10.4.255.150", "gateway": "10.4.255.149", "lan": ["10.4.37.0", "10.4.37.1", "10.4.37.3"]},
    "Moshi": {"wan": "10.6.255.106", "gateway": "10.6.255.105", "lan": ["10.6.24.0", "10.6.24.1", "10.6.24.3"]},
    "Tanga": {"wan": "10.7.255.90", "gateway": "10.7.255.89", "lan": ["10.7.21.0", "10.7.21.1", "10.7.21.3"]}
}

def ping_ip(ip: str) -> dict:
    """Ping a single IP on Windows and return status."""
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "800", ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        status = "ACTIVE ✅" if "TTL=" in result.stdout else "INACTIVE ❌"
        return {"ip": ip, "status": status}
    except Exception as e:
        return {"ip": ip, "status": f"ERROR ({e})"}

def background_ping_job():
    """Continuously ping all IPs and send results to cloud."""
    while True:
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_info = {}
            for region, info in regions.items():
                # WAN
                future_to_info[executor.submit(ping_ip, info["wan"])] = (region, "WAN", info["wan"])
                # Gateway
                future_to_info[executor.submit(ping_ip, info["gateway"])] = (region, "Gateway", info["gateway"])
                # LAN
                for ip in info["lan"]:
                    future_to_info[executor.submit(ping_ip, ip)] = (region, "LAN", ip)

            # Process completed futures
            for future in concurrent.futures.as_completed(future_to_info):
                region, label, ip = future_to_info[future]
                result = future.result()
                result["label"] = label
                results.setdefault(region, []).append(result)
                print(f"[{label}] Region: {region}, IP: {ip}, Status: {result['status']}")

        # Send results to cloud
        try:
            resp = requests.post(cloud_url, json=results, timeout=5)
            print(f"Sent results to cloud, status code: {resp.status_code}")
        except Exception as e:
            print("Failed to send results to cloud:", e)

        time.sleep(ping_interval)

if __name__ == "__main__":
    # Run background ping thread
    thread = threading.Thread(target=background_ping_job, daemon=True)
    thread.start()

    print("Ping client started. Press Ctrl+C to stop.")

    # Keep main thread alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Ping client stopped by user.")
