# =========================
# JOB ALERT SYSTEM
# =========================
# Copy this repo structure locally or into GitHub
#
# Files:
# - main.py
# - companies.json
# - requirements.txt
# - .github/workflows/jobs.yml
#
# =========================

# =========================
# main.py
# =========================
import json
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

KEYWORDS = [
    "project manager",
    "program manager",
    "technical program manager",
    "implementation",
    "implementation manager",
    "delivery manager",
    "product operations",
    "scrum master",
    "agile",
    "tpm",
    "customer success manager",
    "solutions consultant",
    "engagement manager"
]

SEEN_FILE = "seen_jobs.json"


def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except:
        return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def score_job(title):
    score = 0
    title_lower = title.lower()

    for keyword in KEYWORDS:
        if keyword in title_lower:
            score += 10

    if "senior" in title_lower:
        score += 3
    if "principal" in title_lower:
        score += 5

    return score


def scrape_jobs(url):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)

        links = page.query_selector_all("a")
for link in links:
    try:
        title = link.inner_text()
        href = link.get_attribute("href")

        if title and href:
            href = urljoin(url, href)
            results.append({"title": title, "link": href})

    except:
        continue

        browser.close()

    return results


def send_email(new_jobs):
    if not new_jobs:
        return

    body = "\n\n".join([
        f"{job['title']}\n{job['link']} (Score: {job['score']})"
        for job in new_jobs
    ])

    msg = MIMEText(body)
    msg["Subject"] = "New Job Alerts"
    msg["From"] = "millerbrian62@gmail.com"
    msg["To"] = "millerbrian62@gmail.com"

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("millerbrian62@gmail.com", "ioujtqlxumhnqwqu")
        server.send_message(msg)


def main():
    with open("companies.json") as f:
        companies = json.load(f)

    seen = load_seen()
    new_seen = set(seen)
    matched_jobs = []

    for company in companies:
        print(f"Checking {company['name']}...")
        jobs = scrape_jobs(company["url"])

        for job in jobs:
            job_id = job["link"]

            if job_id in seen:
                continue

            score = score_job(job["title"])

            if score >= 10:
                job["score"] = score
                matched_jobs.append(job)
                new_seen.add(job_id)

    matched_jobs.sort(key=lambda x: x["score"], reverse=True)

    send_email(matched_jobs[:10])
    save_seen(new_seen)


if __name__ == "__main__":
    main()
