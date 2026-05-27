# Script mejorado para ejecutar Nacional Colombia Scraper
# Versión robusta para Task Scheduler

# Variables
$ApiUrl = "http://localhost:8000/api/v1/scrape/run?source=nacional_colombia"
$SlackWebhook = $env:SLACK_WEBHOOK_URL  # Set via environment variable
$LogPath = "$env:TEMP\grantflow-scraper.log"

# Timestamp
$StartTime = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"

try {
    # Ejecutar scraper
    Write-Host "Iniciando scraper Nacional Colombia..."
    $Response = Invoke-WebRequest -Uri $ApiUrl -Method POST -ErrorAction Stop
    $Content = $Response.Content | ConvertFrom-Json

    $Total = $Content.total_persisted
    $Duration = $Content.duration_sec
    $Status = "✅ Exitoso"

    Write-Host "Scraper completado: $Total oportunidades persistidas"

} catch {
    $Total = 0
    $Duration = 0
    $Status = "❌ Error: $($_.Exception.Message)"

    Write-Host "Error en scraper: $($_.Exception.Message)"
}

# Timestamp finalización
$EndTime = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"

# Construir mensaje Slack
$SlackPayload = @{
    text = "🇨🇴 Nacional Colombia - Scraper Report"
    blocks = @(
        @{
            type = "header"
            text = @{
                type = "plain_text"
                text = "🇨🇴 Nacional Colombia Scraper"
                emoji = $true
            }
        },
        @{
            type = "section"
            fields = @(
                @{
                    type = "mrkdwn"
                    text = "*Status:*`n$Status"
                },
                @{
                    type = "mrkdwn"
                    text = "*Nuevas opps:*`n$Total"
                },
                @{
                    type = "mrkdwn"
                    text = "*Duración:*`n$($Duration)s"
                },
                @{
                    type = "mrkdwn"
                    text = "*Hora:*`n$EndTime"
                }
            )
        }
    )
} | ConvertTo-Json -Depth 10

# Enviar a Slack
try {
    $SlackResponse = Invoke-WebRequest -Uri $SlackWebhook `
        -Method POST `
        -Body $SlackPayload `
        -ContentType "application/json" `
        -ErrorAction Stop

    Write-Host "Mensaje enviado a Slack ✅"
} catch {
    Write-Host "Error enviando a Slack: $($_.Exception.Message)"
}

# Log
Add-Content -Path $LogPath -Value "[$(Get-Date)] Status: $Status | Total: $Total | Duration: $Duration"

exit 0
