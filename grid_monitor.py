import time
import urllib.request
import urllib.parse

# ==========================================
# 1. TELEGRAM SETTINGS (PASTE YOURS HERE)
# ==========================================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
CHAT_ID = "YOUR_CHAT_ID_HERE"

# ==========================================
# 2. NODE IPS & THRESHOLDS
# ==========================================
NODES = {
    "node1": "http://192.168.10.105/",
    "node2": "http://192.168.10.104/",
    "gateway": "http://192.168.10.103/",
}

SYSTEM_OFF_VOLTAGE = 5.0  
FAULT_VOLTAGE = 13.5      
NODE1_HIGH = 0.55         
NODE2_LOW = 0.25          

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def read(url):
    """Reads data from ESP32. Returns None if disconnected."""
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as r:
                return float(r.read().decode().strip())
        except Exception:
            time.sleep(1)
    return None 

def send_telegram_alert(message):
    """Sends a message to your Telegram phone."""
    encoded_msg = urllib.parse.quote(message)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={encoded_msg}&parse_mode=Markdown"
    try:
        urllib.request.urlopen(url, timeout=20)
        print("📱 Telegram alert sent successfully!")
    except Exception as e:
        print("Failed to send Telegram alert:", e)

# ==========================================
# 4. MAIN LOGIC
# ==========================================
fault_count = 0
fault_alert_sent = False 
node_error_sent = False 

def check():
    global fault_count, fault_alert_sent, node_error_sent
    
    n1 = read(NODES["node1"])
    n2 = read(NODES["node2"])
    v = read(NODES["gateway"])

    # --- A. Check for Disconnected Nodes ---
    if n1 is None or n2 is None or v is None:
        print("!!! ERROR: NODE DISCONNECTED !!!")
        fault_count = 0
        
        if not node_error_sent:
            msg = "⚠️ *GRIDWATCH WARNING* ⚠️\n\nA sensor node has disconnected! Check system power."
            send_telegram_alert(msg)
            node_error_sent = True 
        return

    # Reset node error if all nodes are back online
    node_error_sent = False

    # Print live readings
    print(f"Node1 {n1:.3f} A   Node2 {n2:.3f} A   Source {v:.2f} V")

    # --- B. Check if Transformer is OFF ---
    if v < SYSTEM_OFF_VOLTAGE:
        print("--- System OFF (No Power) ---")
        fault_count = 0
        fault_alert_sent = False 
        return

    # --- C. Check for Line Fault ---
    is_fault = v < FAULT_VOLTAGE and n1 > NODE1_HIGH and n2 < NODE2_LOW

    if is_fault:
        fault_count += 1
    else:
        fault_count = 0
        fault_alert_sent = False 

    # --- D. Trigger Fault Alert (Debounce) ---
    if fault_count >= 3:
        print(">>> FAULT detected between Node 1 and Node 2")
        if not fault_alert_sent:
            print(f"[{time.strftime('%H:%M:%S')}] Sending Telegram alert...")
            msg = "🚨 *GRIDWATCH ALERT* 🚨\n\nFault detected between Node 1 and Node 2!\n\nPlease dispatch a repair crew."
            send_telegram_alert(msg)
            fault_alert_sent = True 
    else:
        print("Normal (Power ON)")

# ==========================================
# 5. START PROGRAM
# ==========================================
if __name__ == "__main__":
    print("Starting GridWatch Monitor...")
    while True:
        try:
            check()
        except KeyboardInterrupt:
            print("\nMonitor stopped.")
            break
        except Exception as e:
            print("Unexpected error:", e)
        
        time.sleep(2)