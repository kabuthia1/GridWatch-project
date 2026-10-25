import time
import urllib.request
import urllib.parse

# ==========================================
# 1. TELEGRAM SETTINGS (PASTE YOURS HERE)
# ==========================================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
CHAT_ID = "YOUR_CHAT_ID_HERE"
# 2. NODE IPS & THRESHOLDS
# ==========================================
NODES = {
    "node1": "http://192.168.10.105/",
    "node2": "http://192.168.10.104/",
    "gateway": "http://192.168.10.103/",
}

# Self-Calibrating Voltage Logic
NORMAL_BASELINE_V = None
VOLTAGE_DROP_MARGIN = 1.0 

NODE1_HIGH = 0.55         
NODE2_LOW = 0.25          

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def read(url):
    """Reads data from ESP32. Returns 0.0 if disconnected to prevent crashes."""
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as r:
                text = r.read().decode().strip()
                if not text or text.lower() == "none":
                    return 0.0
                return float(text)
        except Exception:
            time.sleep(1)
    return None 

def send_telegram_alert(message):
    """Sends a message to your Telegram phone, with a retry mechanism."""
    encoded_msg = urllib.parse.quote(message)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={encoded_msg}&parse_mode=Markdown"
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            urllib.request.urlopen(url, timeout=15)
            print("📱 Telegram alert sent successfully!")
            return True # Success! Exit the function
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print("Retrying in 5 seconds...")
                time.sleep(5) # Wait 5 seconds before trying again
            else:
                print("❌ CRITICAL: Failed to send Telegram alert after 5 attempts.")
    
    return False
# ==========================================
# 4. MAIN LOGIC
# ==========================================
fault_count = 0
fault_alert_sent = False 
node_error_sent = False 

def check():
    global fault_count, fault_alert_sent, node_error_sent, NORMAL_BASELINE_V
    
    n1 = read(NODES["node1"])
    n2 = read(NODES["node2"])
    v = read(NODES["gateway"])

    # --- A. Check for Disconnected Nodes ---
   if n1 is None or n2 is None or v is None or n1 == 0.0 or n2 == 0.0 or v == 0.0:
        print("!!! ERROR: NODE DISCONNECTED OR TIMEOUT !!!")
        fault_count = 0
        try:
            if not node_error_sent:
                send_telegram_alert("⚠️ *GRIDWATCH WARNING* ⚠️\n\nA sensor node has disconnected!")
                node_error_sent = True 
        except Exception:
            pass 
        return

    node_error_sent = False

    # --- B. Self-Calibration Logic ---
    if NORMAL_BASELINE_V is None and n1 < NODE1_HIGH and n2 > NODE2_LOW and v > 5.0:
        NORMAL_BASELINE_V = v
        print(f"⚙️ CALIBRATING: Normal voltage set to {v:.2f} V")
        return

    # --- C. Print Readings (SAFELY) ---
    # We check if NORMAL_BASELINE_V exists before formatting it
    baseline_text = f"{NORMAL_BASELINE_V:.2f} V" if NORMAL_BASELINE_V is not None else "Not Set"
    print(f"Node1 {n1:.3f} A   Node2 {n2:.3f} A   Source {v:.2f} V (Baseline: {baseline_text})")

    # --- D. Check if Transformer is OFF ---
    if v < 5.0:
        print("--- System OFF (No Power) ---")
        fault_count = 0
        fault_alert_sent = False 
        NORMAL_BASELINE_V = None 
        return
        # --- E. Check for Line Fault ---
    # We rely ONLY on the current sensors for fault detection.
    is_fault = (n1 > NODE1_HIGH) and (n2 < NODE2_LOW)

    if is_fault:
        fault_count += 1
    else:
        fault_count = 0
        fault_alert_sent = False 

    # --- F. Trigger Fault Alert (Debounce) ---
    if fault_count >= 3:
        print(">>> FAULT detected between Node 1 and Node 2")
        if not fault_alert_sent:
            print(f"[{time.strftime('%H:%M:%S')}] Sending Telegram alert...")
            try:
                send_telegram_alert("🚨 *GRIDWATCH ALERT* 🚨\n\nFault detected between Node 1 and Node 2!")
            except Exception:
                pass
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







    

  
 
