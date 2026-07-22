#!/usr/bin/env python3
"""
Moltweet automation for ROA Marketing.
Generates tweets via Lyzr inference and can post them when Firebase token is provided.

Usage: python3 moltweet-sync.py [--post]
  Without --post: generates tweet content and saves to file (manual posting)
  With --post: generates AND posts to Moltweet (needs Firebase token)
"""
import subprocess, json, time, os, uuid, random

# ── Config ──
JWT = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjZmNjU3ZGRiYWJmYmZkOTVhNGVkNjZjMjMyNDExZWFhNjE5OGQ4NGMxYmJkOGEyYTI5M2I4MTVmYjRhOTlhYjEifQ.eyJpZCI6Im1lbV9jbXJ2b3BwenEwM2IwMHR2OTBqNmRhbnd5IiwidHlwZSI6Im1lbWJlciIsImlhdCI6MTc4NDcwMDY5NSwiZXhwIjoxNzg1OTEwMjk1LCJhdWQiOiJhcHBfY20za2Jjb3Q4MDBqcDBzdDVjcjd5OWJ4ZCIsImlzcyI6Imh0dHBzOi8vYXBpLm1lbWJlcnN0YWNrLmNvbSJ9.HfPJmr5Mmnezn6C5BWtVn0R2lu5Jd3B0V3205R2GBQpeeXKEMC1As6nLtEgRN91cNYIo7CVKOkbG7XLiD8CUnS4OEHbWiJq62CKI33ToVMxQ_KRKc3Lp8L_5Nv3Pg_q9pkVpJdjjhSj2e947FRp4cMB_FExhXqECB-gh1ZyeKKXib9n77WPX8FiuMTTD-c5S8Q3DKTUCNkEGlVK31-6_xNdAN8Tw-8k99NgrkS0DC1t7f58by7UEKL8WEohMefCrRxEFGRvHwbgtP3X4PwpEUD1JC2Ywxkkjo7rGcSteaz0ScEV1zILznlBoJjnTNt1UQF2LlyT85cClTOG3IwoM8Q"
LYZR_KEY = "sk-default-THWAg0KdRtbRw3eJBvvkJcin9zDyFDZw"
AGENT_ID = "6a6068db12ba1221a783acc1"
AGENT_BACKEND = "https://agent-prod.studio.lyzr.ai"

# Tweet prompt templates
PROMPTS = [
    "Post a short, punchy tweet about a PPC insight from 2026. Include a real CPC number or stat. Max 240 chars. Make it useful for PPC managers.",
    "Post a tweet about Google Ads bidding strategy for small budgets ($500-2000/mo). One actionable tip. Max 240 chars.",
    "Post a tweet about AI agents in PPC. How they help or what's overhyped. Max 240 chars. Be opinionated.",
    "Post a tweet about a common Google Ads mistake and how to fix it. Max 240 chars.",
    "Post a tweet about SEO and AI Overviews impact in 2026. One stat + one tip. Max 240 chars.",
    "Post a tweet about search term audits. How much waste they find. Max 240 chars.",
    "Post a tweet comparing Google Ads vs Meta Ads for B2B. One clear takeaway. Max 240 chars.",
    "Post a tweet about Quality Score optimization. One quick fix. Max 240 chars.",
]

def generate_tweet(prompt=None):
    if prompt is None:
        prompt = random.choice(PROMPTS)
    
    data = {
        "agent_id": AGENT_ID,
        "session_id": str(uuid.uuid4())[:8],
        "messages": [{"role": "user", "content": prompt}]
    }
    
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{AGENT_BACKEND}/v3/inference/chat/",
         "-H", f"Authorization: Bearer {JWT}",
         "-H", f"x-api-key: {LYZR_KEY}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(data)],
        capture_output=True, text=True, timeout=30
    )
    
    try:
        resp = json.loads(result.stdout)
        return resp.get("response", "").strip()
    except:
        return None

def post_to_moltweet(content, firebase_token=None):
    """Post tweet to Moltweet. Needs Firebase ID token."""
    if not firebase_token:
        # Save for manual posting
        with open("/root/.moltweet-queue.txt", "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M')}] {content}\n\n")
        return {"status": "queued", "content": content}
    
    # TODO: Implement Firebase posting when we have the token
    return {"status": "queued", "content": content, "note": "Firebase posting not yet implemented"}

# ── Main ──
if __name__ == "__main__":
    import sys
    should_post = "--post" in sys.argv
    firebase_token = os.environ.get("MOLTWEET_FIREBASE_TOKEN")
    
    tweet = generate_tweet()
    if tweet:
        print(f"\n📝 Generated: {tweet}")
        result = post_to_moltweet(tweet, firebase_token)
        if result["status"] == "queued":
            print(f"💾 Queued for posting: /root/.moltweet-queue.txt")
    else:
        print("❌ Failed to generate tweet")
