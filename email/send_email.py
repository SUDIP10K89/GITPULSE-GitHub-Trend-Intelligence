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
MONO = "'JetBrains Mono','Fira Code','Cascadia Code',monospace"


def format_growth_badge(growth):
    if growth is None:
        return "new"
    return f"+{growth:,} today"


def format_growth_plain(growth):
    if growth is None:
        return "new"
    return f"+{growth:,} stars"


def format_multiple(multiple):
    if multiple is None:
        return "n/a"
    return f"{multiple:.2f}x growth"


def build_repo_card(repo, rank):
    name = repo.get("name", "Unknown")
    description = repo.get("description", "No description available.")
    language = repo.get("language", "")
    stars = repo.get("stars", 0)
    forks = repo.get("forks", 0)
    growth = repo.get("stars_growth")
    category = repo.get("category", "")
    growth_multiple = repo.get("growth_multiple")
    url = repo.get("url", "#")
    lang_color = language_color(language)
    growth_badge_text = format_growth_badge(growth)
    multiple_text = format_multiple(growth_multiple)

    # Rank colour: gold → silver → bronze → dim
    rank_colors = {1: "#e3b341", 2: "#8b949e", 3: "#da8a4a"}
    rank_color = rank_colors.get(rank, "#484f58")

    lang_badge = f"""
        <span style="display:inline-flex;align-items:center;gap:5px;
            font-size:11px;color:#8b949e;font-family:{FONT};">
          <span style="width:9px;height:9px;border-radius:50%;
              background:{lang_color};display:inline-block;flex-shrink:0;"></span>
          {language}
        </span>""" if language else ""

    category_pill = f"""
        <span style="font-size:11px;font-weight:500;color:#8b949e;
            background:rgba(110,118,129,0.12);border:1px solid #21262d;
            border-radius:2em;padding:2px 10px;font-family:{FONT};">
          {category}
        </span>""" if category else ""

    multiple_color = "#a78bfa" if growth_multiple is not None else "#8b949e"
    multiple_border = "rgba(167,139,250,0.2)" if growth_multiple is not None else "#30363d"
    multiple_bg = "rgba(167,139,250,0.08)" if growth_multiple is not None else "rgba(110,118,129,0.12)"
    multiple_badge = f"""
        <span style="font-size:11px;color:{multiple_color};font-family:{MONO};
            background:{multiple_bg};border:1px solid {multiple_border};
            border-radius:2em;padding:2px 10px;">
          {multiple_text}
        </span>"""

    # Alternating very-subtle row tint
    bg = "#0d1117" if rank % 2 == 1 else "#0a0e14"

    return f"""
    <tr>
      <td style="background:{bg};border-bottom:1px solid #161b22;padding:18px 24px;">

        <!-- top row: rank + name + growth badge -->
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="vertical-align:middle;">
              <span style="font-size:11px;font-weight:700;color:{rank_color};
                  font-family:{MONO};margin-right:10px;">#{rank:02d}</span>
              <a href="{url}"
                 style="font-size:15px;font-weight:600;color:#58a6ff;
                     text-decoration:none;font-family:{FONT};">{name}</a>
            </td>
            <td align="right" style="white-space:nowrap;vertical-align:middle;">
              <span style="font-size:12px;font-weight:600;color:#3fb950;
                  font-family:{MONO};background:rgba(46,160,67,0.1);
                  border:1px solid rgba(46,160,67,0.35);
                  border-radius:2em;padding:3px 12px;">
                {growth_badge_text}
              </span>
            </td>
          </tr>
        </table>

        <!-- description -->
        <p style="margin:9px 0 13px;font-size:13px;color:#6e7681;
            line-height:1.55;font-family:{FONT};">{description}</p>

        <!-- meta row -->
        <table cellpadding="0" cellspacing="0">
          <tr>
            <td style="padding-right:14px;">{lang_badge}</td>
            <td style="padding-right:14px;">
              <span style="font-size:11px;color:#8b949e;font-family:{FONT};">
                &#9733;&nbsp;{stars:,}
              </span>
            </td>
            <td style="padding-right:14px;">
              <span style="font-size:11px;color:#8b949e;font-family:{FONT};">
                &#x2442;&nbsp;{forks:,}
              </span>
            </td>
            <td style="padding-right:14px;">{multiple_badge}</td>
            <td>{category_pill}</td>
          </tr>
        </table>

      </td>
    </tr>
    """


def build_html_email(repos):
    date_str = datetime.utcnow().strftime("%B %d, %Y")
    time_str = datetime.utcnow().strftime("%H:%M UTC")
    cards = "".join(build_repo_card(r, i + 1) for i, r in enumerate(repos))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>GitPulse Daily Digest</title>
</head>
<body style="margin:0;padding:0;background:#010409;font-family:{FONT};">

<table width="100%" cellpadding="0" cellspacing="0" style="background:#010409;">
  <tr>
    <td align="center" style="padding:40px 16px 48px;">

      <table width="640" cellpadding="0" cellspacing="0"
          style="max-width:640px;width:100%;">

        <!-- ── HEADER ───────────────────────────────── -->
        <tr>
          <td style="padding-bottom:4px;">
            <table width="100%" cellpadding="0" cellspacing="0"
                style="background:#0d1117;border:1px solid #21262d;
                       border-radius:8px 8px 0 0;overflow:hidden;">

              <!-- Wordmark row -->
              <tr>
                <td style="padding:22px 28px 0;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td>
                        <div style="font-size:20px;font-weight:700;
                            color:#e6edf3;letter-spacing:-0.3px;">
                          GitPulse
                        </div>
                        <div style="font-size:12px;color:#484f58;
                            font-family:{MONO};margin-top:3px;">
                          daily digest &middot; {date_str}
                        </div>
                      </td>
                      <td align="right" style="vertical-align:top;">
                        <span style="font-size:11px;color:#8b949e;
                            font-family:{MONO};background:#161b22;
                            border:1px solid #30363d;border-radius:6px;
                            padding:5px 12px;white-space:nowrap;">
                          sorted by &#9733; growth
                        </span>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Tab bar -->
              <tr>
                <td style="padding:0 28px;">
                  <table cellpadding="0" cellspacing="0"
                      style="border-top:1px solid #21262d;margin-top:14px;width:100%;">
                    <tr>
                      <td style="padding:10px 0 0;">
                        <span style="display:inline-block;font-size:13px;
                            font-weight:600;color:#e6edf3;font-family:{FONT};
                            border-bottom:2px solid #f78166;
                            padding-bottom:10px;margin-bottom:-1px;">
                          Trending today
                        </span>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

            </table>
          </td>
        </tr>

        <!-- ── REPO LIST ─────────────────────────────── -->
        <tr>
          <td style="border:1px solid #21262d;border-top:none;
              border-radius:0 0 8px 8px;overflow:hidden;">
            <table width="100%" cellpadding="0" cellspacing="0">
              {cards}
            </table>
          </td>
        </tr>

        <!-- ── DIVIDER ────────────────────────────────── -->
        <tr>
          <td style="padding:32px 0 0;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="border-top:1px solid #161b22;"></td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ── FOOTER ─────────────────────────────────── -->
        <tr>
          <td style="padding:20px 0 0;text-align:center;">
            <div style="font-size:12px;color:#30363d;font-family:{MONO};
                line-height:2;">
              GitPulse &middot; Automated Daily Digest<br/>
              Data sourced from GitHub Trending &middot; {time_str}
            </div>
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
    growth_plain = format_growth_plain(repo.get("stars_growth"))
    multiple_plain = format_multiple(repo.get("growth_multiple"))
    plain_body += f"{i}. {repo['name']} ({growth_plain})\n"
    plain_body += f"   {repo.get('description', 'N/A')}\n"
    plain_body += f"   Stars: {repo.get('stars', 0):,}  Forks: {repo.get('forks', 0):,}  {multiple_plain}"
    if repo.get("language"):
        plain_body += f"  Language: {repo['language']}"
    plain_body += f"\n   {repo.get('url', '')}\n\n"


subject = f"GitPulse Daily Digest - {datetime.utcnow().strftime('%b %d, %Y')}"
from_email = os.getenv("SMTP_USER")
subscribers = list(subscribers_collection.find(
    {"active": True},
    {"email": 1, "categories": 1, "category": 1, "_id": 0}
))

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
                # Backward-compatible category handling:
                # - New schema: categories (list)
                # - Old schema: category (string)
                categories = []
                if isinstance(sub.get("categories"), list):
                    categories = [c for c in sub["categories"] if c]
                elif isinstance(sub.get("category"), str) and sub.get("category"):
                    categories = [sub["category"]]

                if categories:
                    filtered_repos = list(collection.find({
                        "category": {"$in": categories},
                        "scraped_at": {
                            "$gte": datetime(today.year, today.month, today.day),
                            "$lt": datetime(today.year, today.month, today.day) + timedelta(days=1)
                        }
                    }).sort("stars_growth", -1))
                else:
                    filtered_repos = repo_list

                personalized_repos = filtered_repos[:10]
                personalized_html = build_html_email(personalized_repos)
                personalized_plain = f"GitPulse Daily Digest - {datetime.utcnow().strftime('%B %d, %Y')}\n"
                if categories:
                    personalized_plain += f"Top 10 repositories for categories: {', '.join(categories)}\n"
                else:
                    personalized_plain += "Top 10 repositories by star growth today\n"
                personalized_plain += "=" * 48 + "\n\n"
                for i, repo in enumerate(personalized_repos, 1):
                    growth_plain = format_growth_plain(repo.get("stars_growth"))
                    multiple_plain = format_multiple(repo.get("growth_multiple"))
                    personalized_plain += f"{i}. {repo['name']} ({growth_plain})\n"
                    personalized_plain += f"   {repo.get('description', 'N/A')}\n"
                    personalized_plain += f"   Stars: {repo.get('stars', 0):,}  Forks: {repo.get('forks', 0):,}  {multiple_plain}"
                    if repo.get("language"):
                        personalized_plain += f"  Language: {repo['language']}"
                    personalized_plain += f"\n   {repo.get('url', '')}\n\n"

                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = from_email
                msg["To"] = sub["email"]
                msg.attach(MIMEText(personalized_plain, "plain"))
                msg.attach(MIMEText(personalized_html, "html"))
                server.send_message(msg)
                sent_count += 1
            except Exception as e:
                print(f"Failed to send to {sub.get('email')}: {e}")
                failed_count += 1

    print(f"Email send complete. Sent: {sent_count}, Failed: {failed_count}")
