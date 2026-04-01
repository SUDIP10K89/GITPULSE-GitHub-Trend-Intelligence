import subprocess
import sys

print("Running RepoRadar pipeline")

scripts = [
    "scraper/scrape_trending.py",
    "classifier/classify.py",
    "analytics/growth.py",
    "email/send_email.py"
]

for script in scripts:
    print(f"\nRunning {script}")
    result = subprocess.run([sys.executable, script])
    
    if result.returncode != 0:
        print(f"Error running {script}")
        break

print("Pipeline completed.")
