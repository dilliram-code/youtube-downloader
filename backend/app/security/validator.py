import ipaddress
import re
import socket
from urllib.parse import urlparse
import shutil
from typing import Tuple, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger

# Denied IP networks (SSRF defense)
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.88.99.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("ff00::/8"),
]

# Supported / permitted domain patterns
ALLOWED_DOMAINS = [
    r"(^|\.)youtube\.com$",
    r"^youtu\.be$",
    r"(^|\.)vimeo\.com$",
    r"(^|\.)dailymotion\.com$",
    r"^dai\.ly$",
    r"(^|\.)soundcloud\.com$",
    r"(^|\.)archive\.org$",
    r"(^|\.)wikimedia\.org$",
    r"^test-media\.local$",  # For local automated testing
]

class SecurityError(Exception):
    pass

class ValidationError(Exception):
    pass

def is_ip_blocked(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False  # Not an IP literal

    for net in BLOCKED_IP_NETWORKS:
        if ip in net:
            return True
    return False

def resolve_and_verify_host(hostname: str) -> bool:
    # Allow mock domain in test environment
    if hostname == "test-media.local":
        return True

    # Check if host is direct IP literal
    try:
        ipaddress.ip_address(hostname)
        # If it is an IP address, verify it's not in blocked networks
        if is_ip_blocked(hostname):
            return False
        return True
    except ValueError:
        pass  # It's a hostname, proceed to DNS resolution

    try:
        addr_info = socket.getaddrinfo(hostname, None)
        for entry in addr_info:
            ip_str = entry[4][0]
            if is_ip_blocked(ip_str):
                logger.warning(f"SSRF blocked: {hostname} resolved to blocked IP {ip_str}")
                return False
        return True
    except socket.gaierror:
        logger.warning(f"DNS resolution failed for hostname: {hostname}")
        return False

def validate_video_url(url: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validates URL syntax, scheme, SSRF risk, and supported provider.
    Returns: (is_valid, normalized_url_or_error_msg, detected_provider)
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty", None

    url = url.strip()
    if len(url) > 2048:
        return False, "URL length exceeds maximum limit of 2048 characters", None

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Malformed URL: {str(e)}", None

    if parsed.scheme.lower() not in ("http", "https"):
        return False, "Only HTTP and HTTPS protocols are permitted", None

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return False, "Invalid or missing hostname in URL", None

    # Check for credentials in URL (e.g. http://user:pass@host)
    if parsed.username or parsed.password:
        return False, "URLs with embedded credentials are not allowed", None

    # Check if direct private IP (immediate SSRF reject)
    if is_ip_blocked(hostname) or hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
        return False, "Direct connection to local/private network addresses is blocked", None

    # Check allowed domains before DNS
    is_allowed = False
    detected_provider = "unknown"

    for pattern in ALLOWED_DOMAINS:
        if re.search(pattern, hostname):
            is_allowed = True
            if "youtube" in hostname or "youtu.be" in hostname:
                detected_provider = "youtube"
            elif "vimeo" in hostname:
                detected_provider = "vimeo"
            elif "dailymotion" in hostname or "dai.ly" in hostname:
                detected_provider = "dailymotion"
            elif "soundcloud" in hostname:
                detected_provider = "soundcloud"
            elif "archive.org" in hostname or "wikimedia.org" in hostname:
                detected_provider = "open_media"
            elif hostname == "test-media.local":
                detected_provider = "mock"
            break

    if not is_allowed:
        return False, f"Domain '{hostname}' is not in the list of authorized media providers", None

    # Check SSRF via DNS resolution
    if not resolve_and_verify_host(hostname):
        return False, "Host is not reachable or resolves to an unauthorized private address", None

    return True, url, detected_provider

def sanitize_filename(title: str, max_length: int = 120) -> str:
    """
    Sanitizes string into safe filesystem name without directory traversal or special characters.
    """
    if not title:
        return "video"
    # Remove traversal sequences
    cleaned = re.sub(r'\.{2,}', '', title)
    # Replace non-alphanumeric (except underscores, hyphens, periods)
    cleaned = re.sub(r'[^\w\s\-\.]', '', cleaned, flags=re.UNICODE)
    cleaned = re.sub(r'[\s]+', '_', cleaned).strip('._-')
    if not cleaned:
        cleaned = "media_file"
    return cleaned[:max_length]

def check_disk_space(target_path: str, required_mb: int) -> bool:
    """
    Checks if target volume has enough free disk space.
    """
    try:
        usage = shutil.disk_usage(target_path)
        free_mb = usage.free // (1024 * 1024)
        return free_mb >= required_mb
    except Exception as e:
        logger.error(f"Error checking disk space: {e}")
        return False
