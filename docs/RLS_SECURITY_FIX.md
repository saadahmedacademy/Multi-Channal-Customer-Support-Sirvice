# Supabase RLS Security Vulnerability - Fix Guide

**Date**: 2026-05-14  
**Severity**: 🔴 **CRITICAL**  
**Status**: ⏳ Pending Fix

---

## 🚨 Vulnerability Summary

**Issue**: Row-Level Security (RLS) is **NOT enabled** on database tables  
**Impact**: Anyone with your project URL can read, edit, and delete ALL data  
**Project**: ai-support-agent (yustvyudjnnfniljznez)  
**Detected**: 2026-04-27 (Supabase Security Advisor)

---

## What is Row-Level Security (RLS)?

**RLS** is a PostgreSQL security feature that controls which rows users can access in a table.

### Without RLS (Current State - VULNERABLE):
```
Internet → Supabase Project URL → Database Tables
         ↓
    ANYONE can access ALL data directly!
```

### With RLS Enabled (Secure):
```
Internet → Supabase Project URL → RLS Policies → Database Tables
         ↓                              ↓
    Blocked by RLS              Only authenticated requests allowed
```

---

## 🔍 Affected Tables

All 7 tables in your database are vulnerable:

1. ❌ `customers` - Customer personal information
2. ❌ `customer_identifiers` - Email addresses, phone numbers
3. ❌ `conversations` - Full conversation history
4. ❌ `messages` - All customer messages
5. ❌ `tickets` - Support ticket details
6. ❌ `knowledge_base` - Product documentation
7. ❌ `processed_messages` - Message processing records

**Risk**: Complete data breach, data deletion, data manipulation

---

## 🔧 How to Fix

### Step 1: Activate Database

1. Go to: https://supabase.com/dashboard/project/yustvyudjnnfniljznez
2. Click **"Resume database"** or **"Unpause"**
3. Wait for database to become active (green status)

### Step 2: Run RLS Fix Script

```bash
cd /home/saadahmed/hk-5
source .venv/bin/activate
python scripts/enable_rls.py
```

**What this script does:**
1. Enables RLS on all 7 tables
2. Creates policies allowing only authenticated access
3. Blocks anonymous/public access
4. Verifies all tables are protected

### Step 3: Verify Fix

```bash
python scripts/check_rls_status.py
```

**Expected output:**
```
✅ All tables have RLS enabled!
```

---

## 🔒 What the Fix Does

### RLS Policies Created

```sql
CREATE POLICY "Service role can do everything"
ON table_name
FOR ALL
TO authenticated, service_role
USING (true)
WITH CHECK (true);
```

**What this means:**
- ✅ Your backend API (using `service_role` key) has full access
- ✅ Authenticated users have access
- ❌ Anonymous users are BLOCKED
- ❌ Public access from browser/client is BLOCKED

---

## 🧪 Testing After Fix

### Test Backend API Still Works

```bash
uvicorn backend.api.main:app --reload --port 8000
curl http://localhost:8000/health
```

**Expected**: All endpoints work normally ✅

---

## 📋 Verification Checklist

- [ ] Database is active (not paused)
- [ ] `enable_rls.py` script completed successfully
- [ ] All 7 tables show "✅ RLS Enabled"
- [ ] Supabase dashboard shows no RLS warnings
- [ ] Backend API health check passes
- [ ] Form submission works

---

## 🆘 Troubleshooting

**Error: "Database not found"**  
→ Database is paused. Activate in Supabase dashboard.

**Backend API Returns 403**  
→ Verify `DATABASE_URL` in `.env` uses correct credentials.

**Supabase Still Shows Warning**  
→ Wait 5-10 minutes for cache to clear.

---

## 📖 Resources

- [Supabase RLS Docs](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL RLS Docs](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

---

**Priority**: 🔴 CRITICAL - Fix immediately  
**Estimated Time**: 5 minutes
