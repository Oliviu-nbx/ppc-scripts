#!/bin/bash
# Daily AI bot hit counter from nginx logs
LOG="/var/log/nginx/access.log"
BOTS="GPTBot|ClaudeBot|ChatGPT-User|PerplexityBot|OAI-SearchBot|anthropic-ai|CCBot|Google-Extended|meta-externalagent|Amazonbot|Applebot|Bytespider"
DATE=$(date +%Y-%m-%d)
COUNT=$(grep -c "$DATE" "$LOG" 2>/dev/null)
AICOUNT=$(grep "$DATE" "$LOG" 2>/dev/null | grep -cE "$BOTS")
echo "$DATE | Total: $COUNT | AI Bots: $AICOUNT"
