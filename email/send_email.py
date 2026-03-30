import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

# MongoDB connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]
collection = db["trending_repos"]
subscribers_collection = db["subscribers"]

today = datetime.utcnow().date()

# Get repos and sort by star growth
repos = collection.find({
    "scraped_at": {
        "$gte": datetime(today.year, today.month, today.day),
        "$lt": datetime(today.year, today.month, today.day) + timedelta(days=1)
    }
}).sort("stars_growth", -1)

repo_list = []
for repo in repos:
    if len(repo_list) >= 10:
        break
    repo_list.append(repo)


def language_color(lang):
    colors = {
        "Python": "#3572A5",
        "JavaScript": "#f1e05a",
        "TypeScript": "#3178c6",
        "Rust": "#dea584",
        "Go": "#00ADD8",
        "Java": "#b07219",
        "C++": "#f34b7d",
        "C": "#555555",
        "Ruby": "#701516",
        "Swift": "#F05138",
        "Kotlin": "#A97BFF",
        "Dart": "#00B4AB",
        "Shell": "#89e051",
    }
    return colors.get(lang, "#8b949e")


FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


def build_repo_card(repo, rank):
    name = repo.get("name", "Unknown")
    description = repo.get("description", "No description available.")
    language = repo.get("language", "")
    stars = repo.get("stars", 0)
    forks = repo.get("forks", 0)
    growth = repo.get("stars_growth", 0)
    category = repo.get("category", "")
    url = repo.get("url", "#")
    lang_color = language_color(language)

    lang_badge = f"""<span style="display:inline-flex;align-items:center;gap:6px;font-size:12px;
            color:#8b949e;font-family:{FONT};">
            <span style="width:10px;height:10px;border-radius:50%;background:{lang_color};
                display:inline-block;flex-shrink:0;"></span>{language}
        </span>""" if language else ""

    category_pill = f"""<span style="font-size:11px;font-weight:500;color:#8b949e;
            background:rgba(110,118,129,0.1);border:1px solid #30363d;
            border-radius:2em;padding:2px 10px;font-family:{FONT};">
            {category}
        </span>""" if category else ""

    return f"""
    <tr>
      <td>
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
            style="background:#0d1117;border-bottom:1px solid #21262d;">
          <tr>
            <td style="padding:16px 24px;">

              <!-- Repo name row -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <span style="font-size:12px;color:#6e7681;font-family:monospace;
                        margin-right:8px;">#{rank}</span>
                    <a href="{url}" style="font-size:15px;font-weight:600;color:#58a6ff;
                        text-decoration:none;font-family:{FONT};">{name}</a>
                  </td>
                  <td align="right" style="white-space:nowrap;">
                    <span style="font-size:12px;font-weight:600;color:#3fb950;font-family:monospace;
                        background:rgba(46,160,67,0.1);border:1px solid rgba(46,160,67,0.4);
                        border-radius:2em;padding:3px 10px;">
                      +{growth:,} today
                    </span>
                  </td>
                </tr>
              </table>

              <!-- Description -->
              <p style="margin:8px 0 12px;font-size:13px;color:#8b949e;line-height:1.5;
                  font-family:{FONT};">{description}</p>

              <!-- Meta row -->
              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td style="padding-right:16px;">{lang_badge}</td>
                  <td style="padding-right:16px;">
                    <span style="font-size:12px;color:#8b949e;font-family:{FONT};">
                      &#9733; {stars:,}
                    </span>
                  </td>
                  <td style="padding-right:16px;">
                    <span style="font-size:12px;color:#8b949e;font-family:{FONT};">
                      &#x2442; {forks:,}
                    </span>
                  </td>
                  <td>{category_pill}</td>
                </tr>
              </table>

            </td>
          </tr>
        </table>
      </td>
    </tr>
    """


def build_html_email(repos):
    date_str = datetime.utcnow().strftime("%B %d, %Y")
    cards = "".join(build_repo_card(r, i + 1) for i, r in enumerate(repos))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>GitPulse Daily Digest</title>
</head>
<body style="margin:0;padding:0;background:#010409;">

  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:32px 16px;">
        <table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">

          <!-- HEADER -->
          <tr>
            <td style="padding-bottom:16px;">
              <table width="100%" cellpadding="0" cellspacing="0"
                  style="background:#0d1117;border:1px solid #30363d;border-radius:6px;">
                <tr>
                  <td style="padding:20px 24px 0;">
                    <table width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td>
                          <div style="font-size:18px;font-weight:700;color:#e6edf3;
                              font-family:{FONT};letter-spacing:-0.2px;">
                            GitPulse
                          </div>
                          <div style="font-size:12px;color:#8b949e;font-family:{FONT};margin-top:2px;">
                            Daily Digest &middot; {date_str}
                          </div>
                        </td>
                        <td align="right" style="vertical-align:top;">
                          <span style="font-size:11px;color:#8b949e;font-family:monospace;
                              background:#161b22;border:1px solid #30363d;
                              border-radius:6px;padding:4px 10px;white-space:nowrap;">
                            sorted by star growth
                          </span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <!-- GitHub-style underline tab -->
                <tr>
                  <td style="padding:0 24px;border-top:1px solid #30363d;margin-top:12px;">
                    <span style="display:inline-block;font-size:13px;font-weight:600;
                        color:#e6edf3;font-family:{FONT};
                        border-bottom:2px solid #f78166;padding:10px 0;margin-bottom:-1px;">
                      Trending today
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- REPO LIST — single bordered box like GitHub's file tree -->
          <tr>
            <td style="border:1px solid #30363d;border-radius:6px;overflow:hidden;">
              <table width="100%" cellpadding="0" cellspacing="0">
                {cards}
              </table>
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="padding-top:20px;text-align:center;
                font-size:11px;color:#484f58;font-family:{FONT};line-height:1.8;">
              GitPulse &middot; Automated Daily Digest<br/>
              Data sourced from GitHub Trending &middot; {datetime.utcnow().strftime("%H:%M UTC")}
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

</body>
</html>"""


html_body = build_html_email(repo_list)


plain_body = f"GitPulse Daily Digest - {datetime.utcnow().strftime('%B %d, %Y')}\n"
plain_body += "Top 10 repositories by star growth today\n"
plain_body += "=" * 48 + "\n\n"
for i, repo in enumerate(repo_list, 1):
    plain_body += f"{i}. {repo['name']} (+{repo.get('stars_growth', 0):,} stars)\n"
    plain_body += f"   {repo.get('description', 'N/A')}\n"
    plain_body += f"   Stars: {repo.get('stars', 0):,}  Forks: {repo.get('forks', 0):,}"
    if repo.get("language"):
        plain_body += f"  Language: {repo['language']}"
    plain_body += f"\n   {repo.get('url', '')}\n\n"


subject = f"GitPulse Daily Digest - {datetime.utcnow().strftime('%b %d, %Y')}"
from_email = os.getenv("SMTP_USER")
subscribers = list(subscribers_collection.find({"active": True}, {"email": 1, "_id": 0}))

if not subscribers:
    print("No active subscribers found. No emails were sent.")
else:
    sent_count = 0
    failed_count = 0

    with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))) as server:
        server.starttls()
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        for sub in subscribers:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = from_email
                msg["To"] = sub["email"]
                msg.attach(MIMEText(plain_body, "plain"))
                msg.attach(MIMEText(html_body, "html"))
                server.send_message(msg)
                sent_count += 1
            except Exception as e:
                print(f"Failed to send to {sub.get('email')}: {e}")
                failed_count += 1

    print(f"Email send complete. Sent: {sent_count}, Failed: {failed_count}")
