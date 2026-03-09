# Stop existing node processes
Stop-Process -Name "node" -ErrorAction SilentlyContinue -Force
Start-Sleep -Seconds 2

# 1. Start Gateway (Default binding)
$gwArgList = "scripts/run-node.mjs", "gateway"
$gw = Start-Process node -ArgumentList $gwArgList -WorkingDirectory "C:\Users\ainemo\Desktop\Projects\openclaw" -NoNewWindow -PassThru -RedirectStandardOutput "gateway.log" -RedirectStandardError "gateway.err"
Write-Host "Gateway Started (PID: $($gw.Id))"

# Wait for port 18789
Write-Host "Waiting for Gateway on 127.0.0.1..."
$timeout = 60
$portOpen = $false
for ($i = 0; $i -lt $timeout; $i++) {
    $netstat = netstat -ano | findstr "127.0.0.1:18789"
    if ($netstat -match "LISTENING") {
        $portOpen = $true
        break
    }
    Start-Sleep -Seconds 1
}

if (-not $portOpen) {
    Write-Error "Gateway failed to bind 127.0.0.1:18789"
    exit 1
}
Write-Host "Gateway Ready!"

# 2. Start Node/Agent
$nodeArgList = "scripts/run-node.mjs", "node", "run"
$node = Start-Process node -ArgumentList $nodeArgList -WorkingDirectory "C:\Users\ainemo\Desktop\Projects\openclaw" -NoNewWindow -PassThru -RedirectStandardOutput "node.log" -RedirectStandardError "node.err"
Write-Host "Node Started (PID: $($node.Id))"

Start-Sleep -Seconds 10

# 3. Start Bridge
$env:FEISHU_APP_ID = "cli_a91a394c76389cee"
$env:FEISHU_APP_SECRET = "r21wWNXdVQLIbueoAYgFrhTZItOWtZ1b"

# Check IP for whitelist debugging
try {
    $ip = (Invoke-RestMethod "https://api.ipify.org?format=json").ip
    Write-Host "Current Public IP: $ip" -ForegroundColor Cyan
    Write-Host "Make sure this IP is whitelisted in Feishu Console -> Security Settings!" -ForegroundColor Yellow
}
catch {
    Write-Warning "Could not fetch public IP."
}

$bridgeArgList = "skills/lark-integration/scripts/bridge-webhook.mjs"
$bridge = Start-Process node -ArgumentList $bridgeArgList -WorkingDirectory "C:\Users\ainemo\Desktop\Projects\openclaw" -NoNewWindow -PassThru -RedirectStandardOutput "bridge.log" -RedirectStandardError "bridge.err"
Write-Host "Bridge Started (PID: $($bridge.Id))"

Start-Sleep -Seconds 5

# 4. Test
try {
    $body = @{
        schema = "2.0"
        header = @{ event_type = "im.message.receive_v1" }
        event  = @{
            message = @{
                chat_id      = "oc_test_chat_id"
                message_id   = "om_test_script_final"
                message_type = "text"
                content      = '{"text":"Final Script Test"}'
                chat_type    = "p2p"
            }
        }
    } | ConvertTo-Json -Depth 5
    
    $response = Invoke-RestMethod -Uri "http://localhost:3000/webhook" -Method Post -ContentType "application/json" -Body $body
    Write-Host "Webhook Response: $response"
}
catch {
    Write-Error "Webhook failed: $_"
}
