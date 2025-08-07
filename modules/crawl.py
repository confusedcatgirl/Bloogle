import requests, mysql.connector as conn, time, re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

db = conn.connect(
    host="localhost",
    user="crawler",
    password="f_D9zkez?;ySr&;V7Xry"
)
cur = db.cursor()

QUOTA = 10
USER_AGENT = 'blorbot'
HEADER = {
    'User-Agent': USER_AGENT,
    'Accept-Charset': 'utf-8',
    'Cache-Control': 'no-cache',
    'From': 'blorb@confusedblorb.org'
}

crawled_count = 0
running = True
other_domains = []

cur.execute("SELECT * FROM repo.queue LIMIT 1")
waiting_raw = cur.fetchall()
waiting = ['https://www.scrapingcourse.com/ecommerce/']

for index in waiting_raw:
    waiting.append(index[1])
    cur.execute(f"DELETE FROM repo.queue WHERE ID = '{index[0]}'")

del waiting_raw


while (running):
    link = waiting.pop(0)
    domain = link.split("/")[2]

    print(link + ":", end="")

    # First it will check the database, and then, it will either skip it according to the database, or proceed.
    # However should there be no entry for the robots.txt, it should be fetched and processed.
    
    # Disallow: folder/* -> Everything inside that folder is forbidden 
    #
    #
    parsed = urlparse(link)
    path = parsed.path.replace("*", "%")

    cur.execute(f"SELECT COUNT(*) FROM repo.robots WHERE Domain = '{parsed.netloc}'")
    paths = cur.fetchall()
    allowed = []
    forbidden = []
    stopped = False

    if paths[0][0] == 0:
        robots = requests.get(f"https://{parsed.netloc}/robots.txt")

        if robots.status_code != 200:
            print(f" robots.txt: {robots.status_code};", end="")
            continue

        rules = robots.text.lower().split("user-agent:")

        for rule in rules:
            rule = rule.strip()

            if rule.startswith("*") or rule.startswith("blorbot"):
                for rule_pt in rule.split("\n"):
                    if rule_pt.startswith("allow"):
                        rule_link = rule_pt.split(":")[1].strip()
                        if rule_link.endswith("/"): rule_link += "*"
                        forbidden += [rule_link]

                    elif rule_pt.startswith("disallow"):
                        rule_link = rule_pt.split(":")[1].strip()
                        if rule_link.endswith("/"): rule_link += "*"
                        forbidden += [rule_link]
                del rule_link, rule_pt

        if allowed == []: allowed.append("/*")

        # Add the rulez to da database
        for allow in allowed:
            cur.execute("INSERT INTO repo.robots (Domain, Path, Allowed) VALUES (%s, %s, \"True\")", (parsed.netloc, allow))

        for disallow in forbidden:
            cur.execute("INSERT INTO repo.robots (Domain, Path, Allowed) VALUES (%s, %s, \"False\")", (parsed.netloc, disallow))

        # Forbidden checker
        for dset in disallow:
            regex = re.compile(dset)
            if re.match(regex, link):
                print(" Forbidden by robots.txt")
                stopped = True
                break

        db.commit()
    else:
        cur.execute(f"SELECT Path,Allowed FROM repo.robots WHERE AND Domain = '{parsed.netloc}'")
        all_paths = cur.execute()

        # Forbidden checker
        for dset in all_paths:
            regex = re.compile(dset[0])
            if re.match(regex, link) and dset[1] == "False":
                print(" Forbidden by robots.txt")
                stopped = True
                break

    # Check here for the following: It's not in repo.queue, It's not in repo.raw either.
    cur.execute(f"SELECT * FROM repo.queue WHERE Link LIKE '%{link}'")
    queue = cur.fetchall()

    cur.execute(f"SELECT * FROM repo.raw WHERE Link LIKE '%{link}'")
    raw = cur.fetchall()

    if queue == [] and raw == []:
        
        r = requests.get(link)

        if r.status_code != 200:
            print(f" {r.status_code} -> Skipping")
            continue

        print(f" {r.status_code} -> Scraping")
        del queue, raw

        crawled_count += 1
        soup = BeautifulSoup(r.text, features="html.parser")

        lang = "en-US"
        if soup.html: lang = soup.html["lang"]

        # Collect Data
        website = (link,
                r.text,
                lang,
                time.strftime('%Y-%m-%d %H:%M:%S'))
                # Link, HTML, Language, LastUpdate
        cur.execute("INSERT INTO repo.raw (ID, Link, HTML, Language, LastUpdate) VALUES (UUID(), %s, %s, %s, %s)", website)
        db.commit()

        # Collect all Links
        links = []
        clean_links = []
        for a in soup.find_all(href=True):
            links.append(a['href'])

        # Clean up Links
        for _link in links:
            if _link.startswith("//"): _link = "https:" + _link

            if not (_link.startswith("#") or _link.startswith("?") or _link.startswith("/")) and len(_link) > 5:
                _link_domain = _link.split("/")[2]

                if _link_domain != domain:
                    other_domains.append(_link)
                # Check if it's not in the internal queue.
                if _link not in waiting and ".css" not in _link and ".js" not in _link and ".pdf" not in _link and _link not in other_domains:
                    clean_links.append(_link)

        waiting.extend(clean_links)
    else:
        print(" Skipping, in list already...")

    if len(waiting) == 0:
        running = False

    if crawled_count >= QUOTA:
        running = False
        print("Max reached, stopping...")
        break

    time.sleep(1)

for item in waiting:
    try:
        cur.execute("INSERT INTO repo.queue (Link, AddDate) VALUES (%s, %s)", (item, time.strftime('%Y-%m-%d %H:%M:%S')))
    except: continue
        
for item in other_domains:
    try:
        cur.execute("INSERT INTO repo.queue (Link, AddDate) VALUES (%s, %s)", (item, time.strftime('%Y-%m-%d %H:%M:%S')))
    except: continue

db.commit()
db.close()
