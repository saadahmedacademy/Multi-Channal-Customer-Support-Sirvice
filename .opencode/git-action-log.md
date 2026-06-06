1 ```Run pip-audit -r backend/requirements.txt
Found 40 known vulnerabilities in 6 packages
Name             Version ID             Fix Versions
---------------- ------- -------------- ------------
fastapi          0.109.0 PYSEC-2024-38  0.109.1
python-multipart 0.0.6   PYSEC-2024-38  0.0.7
python-multipart 0.0.6   CVE-2024-53981 0.0.18
python-multipart 0.0.6   CVE-2026-24486 0.0.22
python-multipart 0.0.6   CVE-2026-40347 0.0.26
python-multipart 0.0.6   CVE-2026-42561 0.0.27
aiohttp          3.9.1   PYSEC-2024-24  3.9.2
aiohttp          3.9.1   PYSEC-2024-24  3.9.2
aiohttp          3.9.1   PYSEC-2024-26  3.9.2
aiohttp          3.9.1   PYSEC-2024-26  3.9.2
aiohttp          3.9.1   CVE-2026-34515 3.13.4
aiohttp          3.9.1   CVE-2026-34513 3.13.4
aiohttp          3.9.1   CVE-2026-34516 3.13.4
aiohttp          3.9.1   CVE-2026-34517 3.13.4
aiohttp          3.9.1   CVE-2026-34519 3.13.4
aiohttp          3.9.1   CVE-2026-34518 3.13.4
aiohttp          3.9.1   CVE-2024-27306 3.9.4
aiohttp          3.9.1   CVE-2026-34520 3.13.4
aiohttp          3.9.1   CVE-2024-30251 3.9.4
aiohttp          3.9.1   CVE-2026-34525 3.13.4
aiohttp          3.9.1   CVE-2024-52304 3.10.11
aiohttp          3.9.1   CVE-2025-53643 3.12.14
aiohttp          3.9.1   CVE-2025-69223 3.13.3
aiohttp          3.9.1   CVE-2025-69224 3.13.3
aiohttp          3.9.1   CVE-2025-69228 3.13.3
aiohttp          3.9.1   CVE-2025-69229 3.13.3
aiohttp          3.9.1   CVE-2025-69230 3.13.3
aiohttp          3.9.1   CVE-2025-69226 3.13.3
aiohttp          3.9.1   CVE-2025-69227 3.13.3
aiohttp          3.9.1   CVE-2025-69225 3.13.3
aiohttp          3.9.1   CVE-2026-22815 3.13.4
aiohttp          3.9.1   CVE-2026-34514 3.13.4
aiohttp          3.9.1   CVE-2026-34993 3.14.0
aiohttp          3.9.1   CVE-2026-47265 3.14.0
python-dotenv    1.0.0   CVE-2026-28684 1.2.2
pytest           7.4.4   CVE-2025-71176 9.0.3
starlette        0.35.1  PYSEC-2026-161 1.0.1
starlette        0.35.1  PYSEC-2026-161 1.0.1
starlette        0.35.1  CVE-2024-47874 0.40.0
starlette        0.35.1  CVE-2025-54121 0.47.2
Error: Process completed with exit code 1.```

2 ```0s
Run trufflesecurity/trufflehog@main
Run ##########################################
Error: BASE and HEAD commits are the same. TruffleHog won't scan anything. Please see documentation (https://github.com/trufflesecurity/trufflehog#octocat-trufflehog-github-action).
Error: Process completed with exit code 1.
0s
0s```

3 ```1s
Current runner version: '2.334.0'
Runner Image Provisioner
Operating System
Runner Image
GITHUB_TOKEN Permissions
Secret source: Actions
Prepare workflow directory
Prepare all required actions
Getting action download info
Error: This request has been automatically failed because it uses a deprecated version of `actions/upload-artifact: v3`. Learn more: https://github.blog/changelog/2024-04-16-deprecation-notice-v3-of-the-artifact-actions/
```

4 ```0s
Run if [ "failure" != "success" ] || \
⚠️ Some security scans failed or found issues
Error: Process completed with exit code 1.
0s``` 