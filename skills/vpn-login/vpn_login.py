import os
import sys
import time
import subprocess
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def run_applescript(script):
    process = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    if process.returncode != 0:
        raise Exception(f"AppleScript error: {err.decode('utf-8').strip()}")
    return out.decode('utf-8').strip()

def login_sequence(url, account, password):
    print(f"🛡️ Bootstrapping EasyConnect macOS daemon...")
    try:
        subprocess.run(["open", "-a", "EasyConnect"], check=False)
        time.sleep(3)
    except:
        pass

    print(f"🧹 Launching Native System Safari to bypass Sangfor Kernel Routing Blocks...")
    
    applescript_open = f'''
    with timeout of 10 seconds
        tell application "Safari"
            activate
            set fullTarget to "{url}"
            
            if (count of windows) = 0 then
                make new document with properties {{URL:fullTarget}}
            else
                set targetTab to tab 1 of front window
                set URL of targetTab to fullTarget
                set current tab of front window to targetTab
            end if
        end tell
    end timeout
    '''
    try:
        run_applescript(applescript_open)
    except Exception as e:
        print(f"❌ Failed to open Safari: {e}")
        # Final attempt: force kill and restart
        subprocess.run(["killall", "Safari"], check=False)
        time.sleep(2)
        subprocess.run(["open", "-a", "Safari"], check=False)
        return False

    print("⏳ Waiting for Sangfor Avalon.js to load in Safari...")
    time.sleep(8)
    
    js_payload = f'''
    (function() {{
        try {{
            let account = document.querySelector('input[type="text"][tabindex="1"]');
            let pwd = document.querySelector('input[type="password"][tabindex="2"], #loginPwd');
            if (!account || !pwd) {{
                let relogBtn = Array.from(document.querySelectorAll('button, span, div, a')).find(el => el.textContent && el.textContent.includes('重新登录'));
                if (relogBtn) {{
                    relogBtn.click();
                    return "JS_ERROR:CLICKED_RELOGIN";
                }}
                return "FORM_NOT_FOUND";
            }}
            
            let nativeSet = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
            let triggerEvents = (el) => {{
                el.dispatchEvent(new Event('focus', {{bubbles: true}}));
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                el.dispatchEvent(new Event('blur', {{bubbles: true}}));
            }};
            
            nativeSet.call(account, '{account}');
            triggerEvents(account);
            
            nativeSet.call(pwd, '{password}');
            triggerEvents(pwd);
            
            let icon = document.querySelector('i.iconfont');
            if (icon) icon.click();
            else {{
                let label = document.querySelector('.login-agree-text');
                if (label) label.click();
            }}
            
            let loginBtn = document.querySelector('button.button--normal, button[type="submit"]');
            if (loginBtn) {{
                loginBtn.focus();
                loginBtn.dispatchEvent(new MouseEvent('mousedown', {{ bubbles: true }}));
                loginBtn.dispatchEvent(new MouseEvent('mouseup', {{ bubbles: true }}));
                loginBtn.click();
            }}
            return "SUCCESS";
        }} catch (err) {{
            return "JS_ERROR:" + err.toString();
        }}
    }})();
    '''
    
    js_payload_escaped = js_payload.replace('"', '\\"')
    applescript_inject = f'''
    with timeout of 15 seconds
        tell application "Safari"
            set js_result to do JavaScript "{js_payload_escaped}" in document 1
            return js_result
        end tell
    end timeout
    '''
    
    login_injected = False
    for attempt in range(15): 
        try:
            result = run_applescript(applescript_inject)
            if "SUCCESS" in result:
                login_injected = True
                break
        except Exception as e:
            print(f"⚠️ JS Injection error: {e}")
            pass
        time.sleep(2)
            
    if not login_injected:
        return False
        
    print("⏳ Waiting for tunnel negotiation...")
    time.sleep(20)
    
    js_tunnel = '''
    (function() {
        try {
            let items = Array.from(document.querySelectorAll('.resource-item, [title*="EasyConnect"], span, div'));
            for (let item of items) {
                if (item.textContent && (item.textContent.includes('EasyConnect') || item.textContent.includes('客户端') || item.textContent.includes('VPN'))) {
                    item.click();
                    return "CLICKED_EASYCONNECT";
                }
            }
            return "NO_RESOURCE_FOUND";
        } catch (err) {
            return "JS_ERROR";
        }
    })();
    '''
    js_tunnel_escaped = js_tunnel.replace('"', '\\"')
    applescript_tunnel = f'''
    tell application "Safari"
        set js_result to do JavaScript "{js_tunnel_escaped}" in document 1
        return js_result
    end tell
    '''
    
    try:
        run_applescript(applescript_tunnel)
    except:
        pass

    time.sleep(10)
    try:
        run_applescript('tell application "System Events" to set visible of process "Safari" to false')
    except:
        pass
    return True

def check_connectivity():
    # Attempt to ping the internal GPU machine or a known internal resource
    try:
        # 10.190.30.220 is a key internal target from secrets.json
        subprocess.run(["ping", "-c", "2", "-W", "2", "10.190.30.220"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

def main():
    from dotenv import load_dotenv
    # Standard OpenClaw secrets path
    env_path = os.path.expanduser("~/.openclaw_secrets/.env")
    load_dotenv(env_path)
    
    vpn_url = os.environ.get("VPN_URL")
    vpn_account = os.environ.get("VPN_ACCOUNT")
    vpn_password = os.environ.get("VPN_PASSWORD")
    vpn_backup_account = os.environ.get("VPN_BACKUP_ACCOUNT")
    vpn_backup_password = os.environ.get("VPN_BACKUP_PASSWORD")

    if not all([vpn_url, vpn_account, vpn_password]):
        print("❌ Missing primary VPN credentials.")
        sys.exit(1)

    print("🚀 Starting 24/7 VPN Watchdog...")
    
    while True:
        if not check_connectivity():
            print(f"⚠️ Connectivity lost. Attempting primary login ({vpn_account})...")
            if not login_sequence(vpn_url, vpn_account, vpn_password):
                if vpn_backup_account and vpn_backup_password:
                    print(f"🔄 Primary failed. Attempting backup login ({vpn_backup_account})...")
                    login_sequence(vpn_url, vpn_backup_account, vpn_backup_password)
            
            # Wait for route propagation
            time.sleep(30)
            if check_connectivity():
                print("✅ VPN Connected and connectivity confirmed.")
            else:
                print("❌ Connectivity check failed after login attempt.")
        else:
            print("💓 Connectivity OK.", flush=True)
            
        time.sleep(300)

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
