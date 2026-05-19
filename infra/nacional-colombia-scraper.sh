#!/bin/bash

# Script: Nacional Colombia Scraper
# Ejecuta el scraper de Nacional Colombia diariamente a las 5am UTC
# Envía notificaciones a Slack con los resultados

set -e

# Variables
API_URL="http://localhost:8000/api/v1/scrape/run?source=nacional_colombia"
SLACK_WEBHOOK="https://hooks.slack.com/services/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"
LOG_FILE="/var/log/grantflow/nacional-colombia-scraper.log"
LOG_DIR=$(dirname "$LOG_FILE")

# Crear directorio de logs si no existe
mkdir -p "$LOG_DIR"

# Timestamp
START_TIME=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

# Ejecutar scraper
RESPONSE=$(curl -s -X POST "$API_URL" 2>&1)
EXIT_CODE=$?

# Timestamp finalización
END_TIME=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

# Parsear respuesta
if [ $EXIT_CODE -eq 0 ]; then
  TOTAL=$(echo "$RESPONSE" | grep -o '"total_persisted":[0-9]*' | grep -o '[0-9]*' || echo "0")
  DURATION=$(echo "$RESPONSE" | grep -o '"duration_sec":[0-9.]*' | grep -o '[0-9.]*' || echo "0")
  ERRORS=$(echo "$RESPONSE" | grep -o '"errors":\[\]' | wc -l)

  STATUS="✅ Exitoso"
  STATUS_EMOJI="✅"

  # Log
  echo "[$(date)] ✅ Nacional Colombia scraper completed - $TOTAL opportunities persisted" >> "$LOG_FILE"
else
  TOTAL="0"
  DURATION="0"
  STATUS="❌ Error"
  STATUS_EMOJI="❌"

  # Log
  echo "[$(date)] ❌ Nacional Colombia scraper failed - Exit code: $EXIT_CODE" >> "$LOG_FILE"
  echo "$RESPONSE" >> "$LOG_FILE"
fi

# Enviar notificación a Slack
SLACK_MESSAGE=$(cat <<EOF
{
  "text": "🇨🇴 Nacional Colombia - Scraper Report",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🇨🇴 Nacional Colombia Scraper",
        "emoji": true
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Status:*\n$STATUS"
        },
        {
          "type": "mrkdwn",
          "text": "*Nuevas opps:*\n$TOTAL"
        },
        {
          "type": "mrkdwn",
          "text": "*Duración:*\n${DURATION}s"
        },
        {
          "type": "mrkdwn",
          "text": "*Hora:*\n$END_TIME"
        }
      ]
    }
  ]
}
EOF
)

curl -X POST "$SLACK_WEBHOOK" \
  -H 'Content-Type: application/json' \
  -d "$SLACK_MESSAGE" \
  >> "$LOG_FILE" 2>&1

exit 0
