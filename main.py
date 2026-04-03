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
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", EMAIL_SENDER)  # Will prompt to confirm in main()

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

def send_email_report(report_body):
    """Sends an email containing the compiled network report."""
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        logging.warning("Email credentials not configured. Skipping email report.")
        return

    subject = "Network Connectivity Report"

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(report_body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        logging.info(f"Email report sent successfully to {EMAIL_RECEIVER}.")
        print(f"Email report sent successfully to {EMAIL_RECEIVER}.")
    except Exception as e:
        logging.error(f"Failed to send email report: {e}")
        print(f"Failed to send email report: {e}")

def main():
    global EMAIL_RECEIVER
    print(f"Network Connectivity Checker started.")
    
    default_email = EMAIL_RECEIVER or ""
    prompt_text = f"Enter the email address to receive reports [{default_email}]: " if default_email else "Enter the email address to receive reports: "
    user_input = input(prompt_text).strip()
    if user_input:
        EMAIL_RECEIVER = user_input
    elif not default_email:
        print("No email receiver provided. Email alerts will be disabled unless configured.")
    
    print(f"\nMonitoring IPs: {IPS_TO_CHECK}")
    print(f"Reports will be sent to: {EMAIL_RECEIVER if EMAIL_RECEIVER else 'None'}\n")
    logging.info("Network Connectivity Checker (One-time check) started.")
    
    report_lines = ["Network Connectivity Report:\n"]
    
    for ip in IPS_TO_CHECK:
        print(f"Checking {ip}...")
        is_up, _ = ping(ip)
        
        if is_up:
            print(f"Connectivity to {ip} is UP.")
            report_lines.append(f"[OK] {ip} is UP.")
        else:
            logging.error(f"Connectivity to {ip} failed. Running traceroute...")
            print(f"Connectivity to {ip} failed. Running traceroute...")
            trace = tracert(ip)
            logging.error(f"Traceroute for {ip}:\n{trace}")
            
            report_lines.append(f"[FAILED] {ip} is DOWN.\nTraceroute:\n{trace}")
            
    compiled_report = "\n".join(report_lines)
    
    print("\n--- Final Report ---")
    print(compiled_report)
    print("--------------------\n")
    
    send_email_report(compiled_report)
    print("Network checker finished.")

if __name__ == "__main__":
    main()
