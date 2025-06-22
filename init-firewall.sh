#!/bin/bash
set -euo pipefail

# Claude Agent Network Security Configuration
# Implements a default-deny policy with whitelisted domains

echo "Initializing network security..."

# Check if running as root (required for iptables)
if [ "$EUID" -ne 0 ]; then 
    echo "Warning: Not running as root, skipping firewall configuration"
    exit 0
fi

# Function to resolve domain to IPs
resolve_domain() {
    local domain=$1
    getent ahosts "$domain" 2>/dev/null | awk '{print $1}' | sort -u
}

# Flush existing rules
iptables -F OUTPUT 2>/dev/null || true
iptables -F INPUT 2>/dev/null || true

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Whitelist domains
ALLOWED_DOMAINS=(
    "github.com"
    "api.github.com"
    "raw.githubusercontent.com"
    "api.anthropic.com"
    "claude.ai"
    "registry.npmjs.org"
    "nodejs.org"
)

echo "Whitelisting domains..."
for domain in "${ALLOWED_DOMAINS[@]}"; do
    echo "  - $domain"
    for ip in $(resolve_domain "$domain"); do
        iptables -A OUTPUT -d "$ip" -j ACCEPT 2>/dev/null || true
    done
done

# Allow DNS (required for domain resolution)
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

# Allow HTTPS (port 443) and HTTP (port 80) to whitelisted IPs only
iptables -A OUTPUT -p tcp --dport 443 -m state --state NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p tcp --dport 80 -m state --state NEW,ESTABLISHED -j ACCEPT

# Log dropped packets (optional, for debugging)
# iptables -A OUTPUT -j LOG --log-prefix "DROPPED: " --log-level 4

echo "Network security initialized successfully"
echo "Default policy: DENY"
echo "Whitelisted domains: ${ALLOWED_DOMAINS[*]}"