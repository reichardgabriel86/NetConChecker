import os
import subprocess
import logging
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# --- Configuration ---
# Provide a comma-separated list of IPs in .env
IPS_TO_CHECK = [ip.strip() for ip in os.getenv("IPS_TO_CHECK", "8.8.8.8, 1.1.1.1").split(",")]

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", EMAIL_SENDER)

# Delay between full check cycles (seconds)
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "300"))

# Configure Logging
logging.basicConfig(
    filename='outages.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def ping(ip):
    """Pings a single IP address."""
    try:
        # Windows ping command: -n 1 (one packet), -w 2000 (2s timeout)
        output = subprocess.run(['ping', '-n', '1', '-w', '2000', ip], capture_output=True, text=True)
        # Windows ping returns 0 even if "Destination host unreachable" depending on routing, 
        # checking output string for 'TTL=' is universally safe for successful replies.
        if "TTL=" in output.stdout:
            return True, output.stdout
        else:
            return False, output.stdout
    except Exception as e:
        return False, str(e)

def tracert(ip):
    """Runs a traceroute to the IP."""
    try:
        # Windows traceroute command: -d (do not resolve names), -h 15 (max 15 hops to save time)
        output = subprocess.run(['tracert', '-d', '-h', '15', ip], capture_output=True, text=True)
        return output.stdout
    except Exception as e:
        return str(e)

def send_email_alert(ip, traceroute_output):
    """Sends an email alert containing the traceroute info."""
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        logging.warning("Email credentials not configured. Skipping email alert.")
        return

    subject = f"Network Outage Alert: {ip}"
    body = f"Connectivity check failed for IP: {ip}\n\nTraceroute Output:\n{traceroute_output}"

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        logging.info(f"Email alert sent successfully to {EMAIL_RECEIVER} for IP {ip}.")
    except Exception as e:
        logging.error(f"Failed to send email alert for IP {ip}: {e}")

def main():
    print(f"Network Connectivity Checker started.")
    print(f"Checking IPs: {IPS_TO_CHECK}")
    logging.info("Network Connectivity Checker started.")
    
    # State tracking to avoid spamming emails for the same outage
    recent_outages = {ip: False for ip in IPS_TO_CHECK}
    
    try:
        while True:
            for ip in IPS_TO_CHECK:
                print(f"Checking {ip}...")
                is_up, _ = ping(ip)
                
                if not is_up:
                    if not recent_outages[ip]:
                        logging.error(f"Connectivity to {ip} failed. Running traceroute...")
                        print(f"Connectivity to {ip} failed. Running traceroute...")
                        
                        trace = tracert(ip)
                        logging.error(f"Traceroute for {ip}:\n{trace}")
                        
                        send_email_alert(ip, trace)
                        recent_outages[ip] = True # Mark as down
                    else:
                        logging.error(f"Connectivity to {ip} is still down.")
                        print(f"Connectivity to {ip} is still down.")
                else:
                    if recent_outages[ip]:
                        logging.info(f"Connectivity to {ip} restored.")
                        print(f"Connectivity to {ip} restored.")
                        # Reset outage flag (optionally you could send a 'Recovery' email here)
                        recent_outages[ip] = False
                        
            print(f"Waiting {CHECK_INTERVAL_SECONDS} seconds for next check...\n")
            time.sleep(CHECK_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print("Stopping network checker...")
        logging.info("Network checker stopped by user.")

if __name__ == "__main__":
    main()
