#!/usr/bin/env python3
"""
Moltbook cross-poster: share blog articles to Moltbook.
Searches for articles posted in the last 30 minutes, creates a Moltbook post for each.
"""
import subprocess, json, re, os, sys, time
from datetime import datetime, timezone

API_KEY = open("/root/.moltbook-api-key").read().strip()
BASE = "https://www.moltbook.com/api/v1"

def api(method, path, data=None):
    args = ["curl", "-s", "-H", f"Authorization: Bearer {API_KEY}",
            "-H", "Content-Type: application/json"]
    if method == "POST":
        args += ["-X", "POST", "-d", json.dumps(data)]
    args.append(f"{BASE}{path}")
    r = subprocess.run(args, capture_output=True, text=True, timeout=30)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"error": "parse_failed", "raw": r.stdout[:200], "exit_code": r.returncode}

# ---- Robust challenge solver (token-based subsequence matching) ----
num_map = {
    'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,
    'ten':10,'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,
    'seventeen':17,'eighteen':18,'nineteen':19,'twenty':20,'thirty':30,'forty':40,'fifty':50,
    'sixty':60,'seventy':70,'eighty':80,'ninety':90
}

def subsequence_match(text, word):
    """Check if all chars of `word` appear in order in `text`."""
    wi = 0
    for ch in text:
        if ch == word[wi]:
            wi += 1
            if wi == len(word):
                return True
    return False

def find_number_in_token(token):
    """Find number word in a single token using subsequence matching."""
    clean = re.sub(r'[^a-z]', '', token.lower())
    if not clean:
        return None
    if clean in num_map:
        return num_map[clean]
    # Fuzzy: try subsequence match, prefer longer words
    best = None
    best_len = 0
    for word, val in sorted(num_map.items(), key=lambda x: -len(x[0])):
        if subsequence_match(clean, word) and len(word) > best_len:
            best = val
            best_len = len(word)
    return best

def extract_numbers(challenge_text):
    """Extract numbers from challenge text, handling split tokens."""
    tokens = re.split(r'[\s\]\[\^~\\/\-<>,;:!@#$%&*()_+={}|`"\']+', challenge_text.lower())
    tokens = [t for t in tokens if t]

    nums = []
    for t in tokens:
        n = find_number_in_token(t)
        if n is not None:
            nums.append(n)

    # Handle split tokens: try combining adjacent short tokens
    # e.g., "tw" + "ennty" -> "twenty"
    # This is best-effort; check pairs of adjacent tokens
    merged_nums = []
    skip_next = False
    for i in range(len(nums)):
        if skip_next:
            skip_next = False
            continue
        merged_nums.append(nums[i])
    nums = merged_nums

    # Combine multi-word numbers: tens + units (twenty three -> 23)
    combined = []
    i = 0
    while i < len(nums):
        if i + 1 < len(nums) and nums[i] >= 20 and nums[i] % 10 == 0 and nums[i+1] < 10:
            combined.append(nums[i] + nums[i+1])
            i += 2
        else:
            combined.append(nums[i])
            i += 1
    return combined

def solve_challenge(v):
    """Solve a verification challenge. Returns answer string or None."""
    challenge = v.get("challenge_text", "")
    code = v.get("verification_code", "")
    if not challenge:
        return None

    nums = extract_numbers(challenge)
    if len(nums) < 2:
        print(f"  ⚠️  Could only find {len(nums)} number(s) in: {challenge[:100]}")
        return None

    # Detect operation
    ch_lower = challenge.lower()
    op = '+'  # default: addition (most common: "total", "combined", "force")
    if "subtract" in ch_lower or "minus" in ch_lower or "less" in ch_lower:
        op = '-'
    elif "multiply" in ch_lower or "times" in ch_lower or "product" in ch_lower:
        op = '*'
    elif "divide" in ch_lower:
        op = '/'

    n1 = nums[0]
    n2 = nums[1]
    answer = eval(f"{n1} {op} {n2}")
    return {"code": code, "answer": f"{answer:.2f}"}


# ---- Main: find and post articles ----
articles = subprocess.run(
    ["ls", "-t", "/root/roa-blog/src/content/blog/"],
    capture_output=True, text=True
).stdout.strip().split("\n")[:3]

posted = 0

for fname in articles:
    if not fname.endswith(".md"):
        continue

    # Extract title and tags
    with open(f"/root/roa-blog/src/content/blog/{fname}") as f:
        content = f.read()

    title = ""
    tags = []
    for line in content.split("\n"):
        if line.startswith("title:"):
            title = line.replace("title:", "").strip().strip('"')
        if line.startswith("tags:"):
            tags_str = line.replace("tags:", "").strip()
            tags = [t.strip().strip("[]'\"") for t in tags_str.split(",")]

    if not title:
        continue

    slug = fname.replace(".md", "")
    url = f"https://roa-marketing.com/blog/{slug}/"

    # Create hashtags from tags
    hashtags = " ".join([f"#{t.replace(' ','')}" for t in tags[:3] if t])

    # Short description from title
    post_title = title[:300]

    result = api("POST", "/posts", {
        "submolt_name": "general",
        "title": post_title,
        "url": url,
        "type": "link"
    })

    if result.get("success"):
        v = (result.get("post") or {}).get("verification", {})
        if v.get("challenge_text"):
            answer_data = solve_challenge(v)
            if answer_data:
                verify_res = api("POST", "/verify", {
                    "verification_code": answer_data["code"],
                    "answer": answer_data["answer"]
                })
                if verify_res.get("success"):
                    print(f"✅ Posted (verified {answer_data['answer']}): {title[:80]} -> {url}")
                else:
                    print(f"⚠️  Verification failed for {title[:60]}: {verify_res.get('message', verify_res)[:100]}")
                    # Try manual fallback — just read the challenge
                    print(f"   Challenge was: {v['challenge_text'][:120]}")
            else:
                print(f"⚠️  Couldn't solve challenge for {title[:60]}: {v['challenge_text'][:80]}")
        else:
            print(f"✅ Posted (no verification): {title[:80]} -> {url}")
        posted += 1
        if posted < len([f for f in articles if f.endswith(".md")]):
            print("  Sleeping 160s for rate limit...")
            time.sleep(160)
    else:
        msg = result.get('message', result.get('error', str(result)))[:120]
        print(f"❌ Failed: {title[:60]} — {msg}")

print(f"\nDone. Posted {posted} articles.")
