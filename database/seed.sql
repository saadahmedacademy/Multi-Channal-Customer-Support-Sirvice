-- Seed Data: Knowledge Base and Test Data
-- Description: Sample data for AI Customer Support Agent
-- Created: 2026-03-25
-- Feature: 001-multi-channel

-- Knowledge Base Entries
-- Note: Using gen_random_uuid() to generate UUIDs automatically
INSERT INTO knowledge_base (title, content, category, created_at, updated_at) VALUES
('Getting an API Key',
 'To get an API key, log into your dashboard at dashboard.example.com, navigate to Settings > API Keys, and click ''Generate New Key''. You can create multiple keys for different environments. Keep your API keys secure and never share them publicly.',
 'howto', NOW(), NOW()),

('API Authentication Methods',
 'Our API supports two authentication methods: API Key authentication (via X-API-Key header) and OAuth 2.0 bearer tokens. API Keys are recommended for server-to-server communication, while OAuth is better for user-facing applications.',
 'feature', NOW(), NOW()),

('Rate Limits',
 'API rate limits vary by plan: Free tier allows 100 requests/minute, Pro allows 1000 requests/minute, and Enterprise has custom limits. Rate limit headers are included in all responses. If you exceed the limit, you''ll receive a 429 Too Many Requests error.',
 'feature', NOW(), NOW()),

('Resetting Your Password',
 'To reset your password, go to the login page and click ''Forgot Password''. Enter your email address and we''ll send you a password reset link. The link expires after 24 hours. For security reasons, passwords must be at least 12 characters.',
 'howto', NOW(), NOW()),

('Understanding Billing and Invoices',
 'Billing occurs monthly on your subscription anniversary date. Invoices are automatically emailed to your billing contact. You can view and download invoices from Settings > Billing. We accept credit cards, bank transfers, and PayPal.',
 'faq', NOW(), NOW()),

('Refund Policy',
 'We offer a 30-day money-back guarantee for new subscriptions. If you''re not satisfied with our service, contact support within 30 days of your initial purchase for a full refund. Refund requests are processed within 5-7 business days.',
 'faq', NOW(), NOW()),

('Troubleshooting API Errors',
 'Common API errors: 400 Bad Request - Check your request format. 401 Unauthorized - Verify your API key. 403 Forbidden - Check permissions. 404 Not Found - Resource doesn''t exist. 429 Too Many Requests - Implement rate limiting. 500 Server Error - Retry with backoff.',
 'troubleshooting', NOW(), NOW()),

('Webhook Configuration',
 'Webhooks allow real-time notifications. Configure in Settings > Webhooks. Each webhook requires a URL endpoint that accepts POST requests with JSON payload. We sign all webhook requests with HMAC-SHA256 using your webhook secret.',
 'howto', NOW(), NOW()),

('Data Export and Portability',
 'You can export your data anytime from Settings > Data Export. Choose from CSV, JSON, or XML formats. Large exports are generated asynchronously and emailed when ready. GDPR users have the right to data portability and deletion.',
 'feature', NOW(), NOW()),

('Account Security Best Practices',
 'Protect your account: 1) Enable two-factor authentication (2FA). 2) Use strong, unique passwords. 3) Review active sessions regularly. 4) Rotate API keys periodically. 5) Use environment-specific keys. 6) Monitor audit logs.',
 'howto', NOW(), NOW());

-- Test Customer (optional - for development)
-- INSERT INTO customers (id, email, phone, name, metadata) VALUES
-- ('00000000-0000-0000-0000-000000000001', 'test@example.com', '+14155551234', 'Test User', '{"timezone": "America/New_York", "language": "en"}');

-- Note: For production, seed knowledge base entries with actual product documentation
-- Run this script with: psql $DATABASE_URL -f database/seed.sql
