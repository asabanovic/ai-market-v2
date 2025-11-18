# Scheduled Jobs

This directory contains scheduled background jobs for AI Pijaca.

## expire_lists.py

Expires shopping lists that have passed their 24-hour TTL.

**Frequency:** Every 10 minutes

**What it does:**
- Finds all ACTIVE shopping lists where `expires_at < now()`
- Updates their status to `EXPIRED`
- Logs the number of lists expired

### Running Manually

```bash
cd /path/to/backend
python3 jobs/expire_lists.py
```

### Setting up Cron (Linux/Mac)

Add to crontab (`crontab -e`):

```bash
# Expire shopping lists every 10 minutes
*/10 * * * * cd /path/to/backend && /usr/bin/python3 jobs/expire_lists.py >> logs/expire_lists.log 2>&1
```

### Setting up on Replit

Add to `.replit` file:

```toml
[deployment]
run = ["python3", "main.py"]

[[deployment.cron]]
schedule = "*/10 * * * *"
command = ["python3", "jobs/expire_lists.py"]
```

### Environment Variables

Make sure your `.env` file is present with `DATABASE_URL` configured.

## Adding More Jobs

Create new Python scripts in this directory following the same pattern:

1. Add shebang: `#!/usr/bin/env python3`
2. Import app context
3. Define job function
4. Add `if __name__ == '__main__'` block
5. Make executable: `chmod +x jobs/your_job.py`
6. Add to cron or deployment config
