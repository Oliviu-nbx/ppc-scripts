#!/usr/bin/env python3
"""
Agent.ai automation for ROA Marketing.
Once the agent is created manually via the web UI, this script handles:
1. API key validation
2. Cross-posting blog articles to agent.ai
3. Agent profile updates
4. Engagement monitoring
"""
import subprocess, json, time, os

# Config
API_KEY = os.environ.get("AGENT_AI_KEY", "NZJOPzQXXcPHftOkrvZ8HFlRX1r01PMzL2rb8jYAxsNW6NXWRM52duYh0OhDnDmk")
BASE = "https://agent.ai/api/v1"
AGENT_NAME = "ROA Marketing Google Ads PPC Expert"
WEBSITE = "https://roa-marketing.com"

def api(method, path, data=None):
    args = ["curl", "-s", "-H", f"Authorization: Bearer {API_KEY}",
            "-H", "Content-Type: application/json"]
    if method == "POST" and data:
        args += ["-X", "POST", "-d", json.dumps(data)]
    elif method == "PATCH":
        args += ["-X", "PATCH", "-d", json.dumps(data)]
    elif method == "DELETE":
        args += ["-X", "DELETE"]
    args.append(f"{BASE}{path}")
    r = subprocess.run(args, capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout) if r.stdout.strip() else {"error": r.stderr, "output": r.stdout[:200]}

def post_article(title, description, url):
    """Cross-post a blog article to agent.ai."""
    # Try the agents/actions endpoint for posting content
    result = api("POST", "/agents/actions/run", {
        "action_name": "create_content",
        "input": {
            "title": title[:200],
            "content": description[:2000],
            "url": url,
            "tags": ["PPC", "Google Ads", "SEO", "AI Agents"],
        }
    })
    return result

# Main
if __name__ == "__main__":
    # Test connection
    print("Testing Agent.ai API...")
    me = api("GET", "/me")
    print(f"  Auth: {'✓' if me.get('id') else '✗ ' + str(me)[:100]}")
    
    # Cross-post latest article
    articles = subprocess.run(
        ["ls", "-t", "/root/roa-blog/src/content/blog/"],
        capture_output=True, text=True
    ).stdout.strip().split("\n")[:1]
    
    for fname in articles:
        if not fname.endswith(".md"): continue
        with open(f"/root/roa-blog/src/content/blog/{fname}") as f:
            content = f.read()
        
        title = ""
        desc = ""
        for line in content.split("\n"):
            if line.startswith("title:"): title = line.split('"')[1] if '"' in line else line.split(":")[1].strip()
            if line.startswith("description:"):
                desc = line.split('"')[1] if '"' in line else line.split(":")[1].strip()
                break
        
        slug = fname.replace(".md", "")
        url = f"https://roa-marketing.com/blog/{slug}/"
        
        print(f"  Posting: {title[:60]}...")
        result = post_article(title, desc, url)
        print(f"  Result: {str(result)[:100]}")
