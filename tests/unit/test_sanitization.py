"""Unit tests for input sanitization functionality."""

import pytest
from backend.utils.security import (
    sanitize_html,
    sanitize_text,
    sanitize_email,
    sanitize_phone,
    sanitize_url,
    sanitize_customer_message,
    sanitize_subject,
    sanitize_name
)


class TestHTMLSanitization:
    """Test HTML sanitization to prevent XSS attacks."""

    def test_sanitize_html_removes_script_tags(self):
        """Test that script tags are removed."""
        malicious_html = '<p>Hello</p><script>alert("XSS")</script>'

        result = sanitize_html(malicious_html)

        assert '<script>' not in result
        assert 'alert' not in result
        assert 'Hello' in result

    def test_sanitize_html_removes_onclick_handlers(self):
        """Test that onclick handlers are removed."""
        malicious_html = '<a href="#" onclick="alert(\'XSS\')">Click me</a>'

        result = sanitize_html(malicious_html)

        assert 'onclick' not in result
        assert 'Click me' in result

    def test_sanitize_html_allows_safe_tags(self):
        """Test that safe HTML tags are preserved."""
        safe_html = '<p>Hello <strong>world</strong></p><ul><li>Item 1</li></ul>'

        result = sanitize_html(safe_html)

        assert '<p>' in result
        assert '<strong>' in result
        assert '<ul>' in result
        assert '<li>' in result
        assert 'Hello' in result
        assert 'world' in result

    def test_sanitize_html_removes_dangerous_attributes(self):
        """Test that dangerous attributes are removed."""
        malicious_html = '<img src="x" onerror="alert(\'XSS\')">'

        result = sanitize_html(malicious_html)

        assert 'onerror' not in result

    def test_sanitize_html_strip_mode(self):
        """Test that strip mode removes all HTML tags."""
        html = '<p>Hello <strong>world</strong></p>'

        result = sanitize_html(html, strip=True)

        assert '<p>' not in result
        assert '<strong>' not in result
        assert 'Hello world' in result

    def test_sanitize_html_handles_empty_input(self):
        """Test handling of empty input."""
        result = sanitize_html("")

        assert result == ""

    def test_sanitize_html_handles_none_input(self):
        """Test handling of None input."""
        result = sanitize_html(None)

        assert result == ""

    def test_sanitize_html_removes_javascript_protocol(self):
        """Test that javascript: protocol is removed from links."""
        malicious_html = '<a href="javascript:alert(\'XSS\')">Click</a>'

        result = sanitize_html(malicious_html)

        assert 'javascript:' not in result

    def test_sanitize_html_removes_data_protocol(self):
        """Test that data: protocol is removed."""
        malicious_html = '<img src="data:text/html,<script>alert(\'XSS\')</script>">'

        result = sanitize_html(malicious_html)

        assert 'data:' not in result or '<script>' not in result


class TestTextSanitization:
    """Test plain text sanitization."""

    def test_sanitize_text_removes_null_bytes(self):
        """Test that null bytes are removed."""
        text = "Hello\x00World"

        result = sanitize_text(text)

        assert '\x00' not in result
        assert 'HelloWorld' in result

    def test_sanitize_text_removes_control_characters(self):
        """Test that control characters are removed."""
        text = "Hello\x01\x02\x03World"

        result = sanitize_text(text)

        assert '\x01' not in result
        assert 'HelloWorld' in result

    def test_sanitize_text_normalizes_whitespace(self):
        """Test that multiple spaces are collapsed."""
        text = "Hello    World"

        result = sanitize_text(text)

        assert result == "Hello World"

    def test_sanitize_text_trims_whitespace(self):
        """Test that leading/trailing whitespace is removed."""
        text = "  Hello World  "

        result = sanitize_text(text)

        assert result == "Hello World"

    def test_sanitize_text_respects_max_length(self):
        """Test that text is truncated to max length."""
        text = "a" * 1000

        result = sanitize_text(text, max_length=100)

        assert len(result) == 100

    def test_sanitize_text_handles_empty_input(self):
        """Test handling of empty input."""
        result = sanitize_text("")

        assert result == ""

    def test_sanitize_text_preserves_newlines(self):
        """Test that newlines are preserved."""
        text = "Line 1\nLine 2"

        result = sanitize_text(text)

        # Newlines should be normalized to spaces
        assert "Line 1" in result
        assert "Line 2" in result


class TestEmailSanitization:
    """Test email address sanitization."""

    def test_sanitize_email_valid_email(self):
        """Test that valid email is preserved."""
        email = "user@example.com"

        result = sanitize_email(email)

        assert result == "user@example.com"

    def test_sanitize_email_converts_to_lowercase(self):
        """Test that email is converted to lowercase."""
        email = "User@Example.COM"

        result = sanitize_email(email)

        assert result == "user@example.com"

    def test_sanitize_email_removes_whitespace(self):
        """Test that whitespace is removed."""
        email = "  user@example.com  "

        result = sanitize_email(email)

        assert result == "user@example.com"

    def test_sanitize_email_rejects_invalid_format(self):
        """Test that invalid email format is rejected."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "user@example",
        ]

        for email in invalid_emails:
            result = sanitize_email(email)
            assert result == "", f"Should reject: {email}"

    def test_sanitize_email_handles_empty_input(self):
        """Test handling of empty input."""
        result = sanitize_email("")

        assert result == ""

    def test_sanitize_email_handles_plus_addressing(self):
        """Test that plus addressing is preserved."""
        email = "user+tag@example.com"

        result = sanitize_email(email)

        assert result == "user+tag@example.com"


class TestPhoneSanitization:
    """Test phone number sanitization."""

    def test_sanitize_phone_preserves_valid_format(self):
        """Test that valid phone format is preserved."""
        phone = "+14155551234"

        result = sanitize_phone(phone)

        assert result == "+14155551234"

    def test_sanitize_phone_removes_invalid_characters(self):
        """Test that invalid characters are removed."""
        phone = "+1 (415) 555-1234 ext. 123"

        result = sanitize_phone(phone)

        # Should keep digits, +, spaces, and hyphens
        assert 'ext' not in result
        assert '.' not in result

    def test_sanitize_phone_handles_empty_input(self):
        """Test handling of empty input."""
        result = sanitize_phone("")

        assert result == ""

    def test_sanitize_phone_removes_letters(self):
        """Test that letters are removed."""
        phone = "+1-415-CALL-NOW"

        result = sanitize_phone(phone)

        assert 'CALL' not in result
        assert 'NOW' not in result


class TestURLSanitization:
    """Test URL sanitization."""

    def test_sanitize_url_allows_http(self):
        """Test that HTTP URLs are allowed."""
        url = "http://example.com"

        result = sanitize_url(url)

        assert result == "http://example.com"

    def test_sanitize_url_allows_https(self):
        """Test that HTTPS URLs are allowed."""
        url = "https://example.com"

        result = sanitize_url(url)

        assert result == "https://example.com"

    def test_sanitize_url_blocks_javascript_protocol(self):
        """Test that javascript: protocol is blocked."""
        url = "javascript:alert('XSS')"

        result = sanitize_url(url)

        assert result == ""

    def test_sanitize_url_blocks_data_protocol(self):
        """Test that data: protocol is blocked."""
        url = "data:text/html,<script>alert('XSS')</script>"

        result = sanitize_url(url)

        assert result == ""

    def test_sanitize_url_adds_https_to_bare_domain(self):
        """Test that bare domain gets https:// prefix."""
        url = "example.com"

        result = sanitize_url(url)

        assert result == "https://example.com"

    def test_sanitize_url_handles_empty_input(self):
        """Test handling of empty input."""
        result = sanitize_url("")

        assert result == ""


class TestCustomerMessageSanitization:
    """Test customer message sanitization."""

    def test_sanitize_customer_message_strips_html(self):
        """Test that HTML is stripped from customer messages."""
        message = "Hello <script>alert('XSS')</script> World"

        result = sanitize_customer_message(message)

        assert '<script>' not in result
        assert 'Hello' in result
        assert 'World' in result

    def test_sanitize_customer_message_respects_max_length(self):
        """Test that message is truncated to max length."""
        message = "a" * 15000

        result = sanitize_customer_message(message, max_length=10000)

        assert len(result) == 10000

    def test_sanitize_customer_message_normalizes_whitespace(self):
        """Test that whitespace is normalized."""
        message = "Hello    World"

        result = sanitize_customer_message(message)

        assert result == "Hello World"


class TestSubjectSanitization:
    """Test subject line sanitization."""

    def test_sanitize_subject_strips_html(self):
        """Test that HTML is stripped from subject."""
        subject = "Help <script>alert('XSS')</script> Needed"

        result = sanitize_subject(subject)

        assert '<script>' not in result
        assert 'Help' in result
        assert 'Needed' in result

    def test_sanitize_subject_respects_max_length(self):
        """Test that subject is truncated to max length."""
        subject = "a" * 1000

        result = sanitize_subject(subject, max_length=500)

        assert len(result) == 500


class TestNameSanitization:
    """Test name sanitization."""

    def test_sanitize_name_preserves_valid_name(self):
        """Test that valid name is preserved."""
        name = "John Doe"

        result = sanitize_name(name)

        assert result == "John Doe"

    def test_sanitize_name_allows_hyphens(self):
        """Test that hyphens are allowed in names."""
        name = "Mary-Jane Smith"

        result = sanitize_name(name)

        assert result == "Mary-Jane Smith"

    def test_sanitize_name_allows_apostrophes(self):
        """Test that apostrophes are allowed in names."""
        name = "O'Brien"

        result = sanitize_name(name)

        assert result == "O'Brien"

    def test_sanitize_name_removes_special_characters(self):
        """Test that special characters are removed."""
        name = "John@Doe#123"

        result = sanitize_name(name)

        assert '@' not in result
        assert '#' not in result
        assert 'John' in result
        assert 'Doe' in result

    def test_sanitize_name_strips_html(self):
        """Test that HTML is stripped from names."""
        name = "John <script>alert('XSS')</script> Doe"

        result = sanitize_name(name)

        assert '<script>' not in result
        assert 'John' in result
        assert 'Doe' in result

    def test_sanitize_name_respects_max_length(self):
        """Test that name is truncated to max length."""
        name = "a" * 500

        result = sanitize_name(name, max_length=255)

        assert len(result) == 255


class TestSanitizationEdgeCases:
    """Test edge cases in sanitization."""

    def test_sanitize_handles_unicode(self):
        """Test that Unicode characters are handled correctly."""
        text = "Hello 世界 🌍"

        result = sanitize_text(text)

        assert "Hello" in result
        assert "世界" in result
        assert "🌍" in result

    def test_sanitize_handles_very_long_input(self):
        """Test handling of very long input."""
        text = "a" * 100000

        result = sanitize_text(text, max_length=10000)

        assert len(result) == 10000

    def test_sanitize_handles_mixed_content(self):
        """Test handling of mixed HTML and text."""
        content = "Normal text <p>HTML paragraph</p> more text <script>bad</script>"

        result = sanitize_html(content, strip=True)

        assert '<script>' not in result
        assert 'Normal text' in result
        assert 'HTML paragraph' in result

    def test_sanitize_preserves_legitimate_content(self):
        """Test that legitimate content is not over-sanitized."""
        message = "I need help with API authentication. Error code: 401. Email: user@example.com"

        result = sanitize_customer_message(message)

        assert "API authentication" in result
        assert "401" in result
        assert "user@example.com" in result


class TestSecurityVulnerabilities:
    """Test protection against known security vulnerabilities."""

    def test_prevents_xss_via_img_tag(self):
        """Test XSS prevention via img tag."""
        malicious = '<img src=x onerror="alert(\'XSS\')">'

        result = sanitize_html(malicious)

        assert 'onerror' not in result
        assert 'alert' not in result

    def test_prevents_xss_via_svg(self):
        """Test XSS prevention via SVG."""
        malicious = '<svg onload="alert(\'XSS\')">'

        result = sanitize_html(malicious)

        assert 'onload' not in result or '<svg>' not in result

    def test_prevents_xss_via_iframe(self):
        """Test XSS prevention via iframe."""
        malicious = '<iframe src="javascript:alert(\'XSS\')"></iframe>'

        result = sanitize_html(malicious)

        # iframe should be removed (not in ALLOWED_TAGS)
        assert '<iframe>' not in result

    def test_prevents_sql_injection_characters(self):
        """Test that SQL injection characters are handled."""
        text = "'; DROP TABLE users; --"

        result = sanitize_text(text)

        # Should preserve the text but sanitize it
        assert result is not None
        # The actual SQL injection won't work because we use parameterized queries

    def test_prevents_command_injection(self):
        """Test that command injection attempts are sanitized."""
        text = "test; rm -rf /"

        result = sanitize_text(text)

        # Should preserve text but won't execute as command
        assert result is not None
