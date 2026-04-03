# Network Connectivity Checker

A lightweight, robust Python script to monitor network connectivity to multiple endpoints. The script iterates through a configured list of IP addresses or hostnames, performs ping checks, and if an outage is detected, records the connectivity state alongside an automated traceroute. After running its sweep, the script compiles a full report of all successful and failed connections, prints it to the console, and sends it directly to your email.

## Features
- Evaluates endpoint reachability using native OS ping commands.
- Automatically captures traceroute output for unreachable endpoints to help pinpoint routing failures.
- Consolidates passes and failures into a unified summary report.
- Seamlessly sends the final report to your provided email address (via SMTP).
- Easy to schedule as a cron job or Windows Scheduled Task since it executes a full check once and safely terminates.

## Setup Instructions

### 1. Requirements
Ensure you have Python 3.x installed. Then install the project dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configuration
Copy the supplied template configuration file to establish your environment variables:
```bash
cp .env.example .env
```
Once copied, open `.env` and fill out your information:
- `IPS_TO_CHECK`: Comma-separated list of IP addresses to monitor.
- `EMAIL_SENDER` and `EMAIL_PASSWORD`: Your email login credentials. If you are using Gmail, this will require generating a 16-character [App Password](https://support.google.com/accounts/answer/185833?hl=en).
- *Optional variables can be updated for STMP hosts/ports depending on your email provider.* 

## Usage
Simply invoke the main script. The script will initially prompt you for a receiver email address (defaults to what is in your `.env` or skips if blank), run its checks, output the report, and terminate upon successfully emailing you.

```bash
python main.py
```
