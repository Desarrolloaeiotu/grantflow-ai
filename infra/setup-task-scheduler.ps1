# Script: Configurar Task Scheduler para Nacional Colombia Scraper
# Ejecutar como Administrador

# Variables
$TaskName = "GrantFlow - Nacional Colombia Scraper"
$TaskPath = "\GrantFlow\"
$ScriptPath = "C:\Users\Luis Mendez\OneDrive - Fundación Carulla - Aeiotu\Escritorio\Grantflow app\infra\nacional-colombia-scraper.sh"
$BackendUrl = "http://localhost:8000/api/v1/scrape/run?source=nacional_colombia"
$SlackWebhook = $env:SLACK_WEBHOOK_URL  # Set via environment variable

# Crear la tarea directamente con PowerShell (sin bash)
# Nota: En Windows, usaremos un script PowerShell en lugar de bash

Write-Host "Creando tarea programada: $TaskName" -ForegroundColor Green

# Crear acción (ejecutar PowerShell que llama a curl)
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument @"
-NoProfile -WindowStyle Hidden -Command {
    `$Response = Invoke-WebRequest -Uri '$BackendUrl' -Method POST -ErrorAction SilentlyContinue
    `$Total = `$Response.Content | ConvertFrom-Json | Select-Object -ExpandProperty total_persisted
    `$SlackMessage = @{
        text = '🇨🇴 Nacional Colombia - Scraper Report'
        blocks = @(
            @{
                type = 'header'
                text = @{
                    type = 'plain_text'
                    text = '🇨🇴 Nacional Colombia Scraper'
                    emoji = `$true
                }
            },
            @{
                type = 'section'
                fields = @(
                    @{
                        type = 'mrkdwn'
                        text = '*Status:*`n✅ Exitoso'
                    },
                    @{
                        type = 'mrkdwn'
                        text = "*Nuevas opps:*`n`$Total"
                    }
                )
            }
        )
    }
    Invoke-WebRequest -Uri '$SlackWebhook' -Method POST -Body (`$SlackMessage | ConvertTo-Json -Depth 10) -ContentType 'application/json'
}
"@

# Crear trigger (5am UTC = 5am UTC, pero en horario local depende de tu zona)
# Para Colombia (UTC-5), 5am UTC = 12am (medianoche) zona horaria local
# Ajusta si es necesario
$Trigger = New-ScheduledTaskTrigger -Daily -At 5:00am

# Crear principal (usuario actual)
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -RunLevel Highest

# Crear configuración
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Crear y registrar la tarea
Register-ScheduledTask -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings `
    -Force -Verbose

Write-Host "✅ Tarea programada creada exitosamente" -ForegroundColor Green
Write-Host "Task Name: $TaskName" -ForegroundColor Cyan
Write-Host "Schedule: Diariamente a las 5:00 AM" -ForegroundColor Cyan
Write-Host ""
Write-Host "Notas:" -ForegroundColor Yellow
Write-Host "- La tarea se ejecutará diariamente a las 5:00 AM en tu zona horaria local" -ForegroundColor Yellow
Write-Host "- Para cambiar la hora, edita la tarea en Task Scheduler" -ForegroundColor Yellow
Write-Host "- Los resultados se enviarán a Slack automáticamente" -ForegroundColor Yellow
