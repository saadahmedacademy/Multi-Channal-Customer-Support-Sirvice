# Secrets Management Guide

**Project**: AI Customer Support Agent  
**Last Updated**: 2026-05-16

---

## Overview

This guide covers how to securely manage secrets and sensitive configuration for the AI Customer Support Agent in production.

---

## Principles

1. **Never commit secrets to git** - Use environment variables
2. **Rotate secrets regularly** - Change API keys and tokens periodically
3. **Use least privilege** - Grant minimum necessary permissions
4. **Separate environments** - Different secrets for dev/staging/production
5. **Audit access** - Track who has access to secrets

---

## Secret Types

### Database Credentials
- **What**: PostgreSQL connection string
- **Format**: `postgresql://user:password@host:port/database`
- **Rotation**: Every 90 days
- **Access**: Backend API, Worker only

### API Keys
- **OpenRouter/Gemini**: AI model access
- **WhatsApp**: Meta Cloud API token
- **Gmail**: OAuth credentials
- **Internal**: API key for protected endpoints

### Application Secrets
- **SECRET_KEY**: Session encryption
- **INTERNAL_API_KEYS**: Internal endpoint authentication

---

## Storage Options

### Option 1: Environment Variables (Current)

**Pros**: Simple, works everywhere  
**Cons**: Visible in process list, no rotation automation

```bash
# .env file (never commit)
DATABASE_URL=postgresql://...
OPENROUTER_API_KEY=sk-or-...
```

### Option 2: Docker Secrets

**Pros**: Encrypted at rest, access control  
**Cons**: Docker Swarm only

```yaml
# docker-compose.yml
secrets:
  db_password:
    external: true
```

### Option 3: GitHub Secrets (CI/CD)

**Pros**: Encrypted, audit log  
**Cons**: Only for GitHub Actions

```yaml
# .github/workflows/deploy.yml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

### Option 4: HashiCorp Vault (Recommended for Production)

**Pros**: Centralized, rotation, audit, encryption  
**Cons**: Additional infrastructure

```python
# Example Vault integration
import hvac
client = hvac.Client(url='https://vault.example.com')
secret = client.secrets.kv.v2.read_secret_version(path='ai-support/prod')
```

---

## Secret Rotation Procedures

### Rotating Database Password

1. Create new password in database
2. Update `.env` with new password
3. Restart services
4. Verify connectivity
5. Remove old password from database

### Rotating API Keys

1. Generate new API key in provider dashboard
2. Add new key to `INTERNAL_API_KEYS` (comma-separated)
3. Deploy with both old and new keys
4. Update clients to use new key
5. Remove old key after 24 hours

### Rotating OAuth Tokens

1. Revoke old OAuth client in Google Cloud Console
2. Create new OAuth client
3. Run `python scripts/get_gmail_token.py`
4. Update `.env` with new credentials
5. Restart services

---

## Access Control

### Who Needs Access

| Secret | Backend | Worker | Frontend | CI/CD |
|--------|---------|--------|----------|-------|
| DATABASE_URL | ✅ | ✅ | ❌ | ✅ |
| AI API Keys | ✅ | ✅ | ❌ | ❌ |
| WhatsApp Token | ✅ | ✅ | ❌ | ❌ |
| Gmail OAuth | ✅ | ✅ | ❌ | ❌ |
| INTERNAL_API_KEYS | ✅ | ❌ | ❌ | ❌ |
| SECRET_KEY | ✅ | ❌ | ❌ | ❌ |

### Access Audit

Track who has access to production secrets:

```bash
# List who can access GitHub secrets
gh secret list --repo owner/repo

# Check who has access to .env file
ls -la .env
```

---

## Generating Secrets

### API Key (64 characters)
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Secret Key (URL-safe)
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Random Password (32 characters)
```bash
python -c "import secrets; import string; chars = string.ascii_letters + string.digits; print(''.join(secrets.choice(chars) for _ in range(32)))"
```

---

## Deployment Checklist

Before deploying to production:

- [ ] All secrets in `.env.production` (not `.env.example`)
- [ ] `.env.production` in `.gitignore`
- [ ] Secrets not in Docker image
- [ ] Secrets not in logs
- [ ] Secrets not in error messages
- [ ] Secrets not in Sentry events (filtered)
- [ ] Database password is strong (16+ chars)
- [ ] API keys are production keys (not test keys)
- [ ] OAuth tokens are fresh (< 30 days old)
- [ ] INTERNAL_API_KEYS are unique per environment

---

## Emergency Procedures

### If Secrets Are Compromised

1. **Immediate**: Revoke compromised secrets
2. **Generate**: Create new secrets
3. **Deploy**: Update production with new secrets
4. **Verify**: Test all integrations
5. **Audit**: Check logs for unauthorized access
6. **Document**: Record incident and response

### If Secrets Are Committed to Git

1. **Remove**: `git rm --cached .env`
2. **Rewrite history**: `git filter-branch` or BFG Repo-Cleaner
3. **Force push**: `git push --force`
4. **Revoke**: Revoke all exposed secrets
5. **Generate**: Create new secrets
6. **Notify**: Inform team and stakeholders

---

## Monitoring

### Alerts to Set Up

- Failed authentication attempts (> 10/min)
- API key usage from unexpected IPs
- Database connection from unknown hosts
- Unusual API call patterns

### Audit Log

Track secret access:

```python
# Log secret access (without logging the secret itself)
logger.info(f"Secret accessed: {secret_name}", extra={
    "user": user_id,
    "ip": request_ip,
    "timestamp": datetime.utcnow()
})
```

---

## Best Practices

1. **Use different secrets per environment**
   - Development: `dev-api-key-...`
   - Staging: `staging-api-key-...`
   - Production: `prod-api-key-...`

2. **Limit secret scope**
   - Use read-only database users where possible
   - Use API keys with minimum required permissions

3. **Automate rotation**
   - Set calendar reminders for manual rotation
   - Use tools like Vault for automatic rotation

4. **Document everything**
   - Where secrets are stored
   - Who has access
   - When they were last rotated

5. **Test secret rotation**
   - Practice rotating secrets in staging
   - Have rollback plan ready

---

## Tools

### Secret Scanning

```bash
# Scan for secrets in git history
trufflehog git file://. --only-verified

# Scan for secrets in files
detect-secrets scan
```

### Secret Management

- **1Password**: Team password manager
- **AWS Secrets Manager**: AWS-native solution
- **HashiCorp Vault**: Enterprise secret management
- **Google Secret Manager**: GCP-native solution

---

## References

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [12-Factor App: Config](https://12factor.net/config)
- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)

---

**Remember**: When in doubt, rotate the secret. It's better to be safe than sorry.
