import pytest
from backend.app.security.validator import (
    validate_video_url,
    sanitize_filename,
    is_ip_blocked
)

def test_blocked_private_ips():
    assert is_ip_blocked("127.0.0.1") is True
    assert is_ip_blocked("10.0.0.1") is True
    assert is_ip_blocked("192.168.1.1") is True
    assert is_ip_blocked("172.16.0.5") is True
    assert is_ip_blocked("169.254.169.254") is True
    assert is_ip_blocked("::1") is True
    # Public IP should not be blocked
    assert is_ip_blocked("8.8.8.8") is False

def test_url_validation_permitted():
    valid, url, provider = validate_video_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert valid is True
    assert provider == "youtube"

    valid, url, provider = validate_video_url("https://youtu.be/dQw4w9WgXcQ")
    assert valid is True
    assert provider == "youtube"

    valid, url, provider = validate_video_url("https://vimeo.com/76979871")
    assert valid is True
    assert provider == "vimeo"

def test_url_validation_rejections():
    # Empty
    valid, msg, _ = validate_video_url("")
    assert valid is False
    assert "empty" in msg

    # File / ftp schemes
    valid, msg, _ = validate_video_url("ftp://youtube.com/video")
    assert valid is False

    valid, msg, _ = validate_video_url("file:///etc/passwd")
    assert valid is False

    # SSRF attempts
    valid, msg, _ = validate_video_url("http://127.0.0.1:8000/api")
    assert valid is False

    valid, msg, _ = validate_video_url("http://localhost:5000/secret")
    assert valid is False

    valid, msg, _ = validate_video_url("http://169.254.169.254/latest/meta-data/")
    assert valid is False

    # Non-permitted domains
    valid, msg, _ = validate_video_url("https://random-untrusted-site.xyz/malicious.mp4")
    assert valid is False
    assert "not in the list of authorized media providers" in msg

def test_sanitize_filename():
    assert sanitize_filename("Simple Title") == "Simple_Title"
    assert sanitize_filename("Title with / slash and .. dots!") == "Title_with_slash_and_dots"
    assert sanitize_filename("../../../etc/passwd") == "etcpasswd"
    assert sanitize_filename("🎵 Amazing 4K 60fps Video! (Official)") == "Amazing_4K_60fps_Video_Official"
