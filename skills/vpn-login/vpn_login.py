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

def main():
    vpn_url = os.environ.get("VPN_URL")
    vpn_account = os.environ.get("VPN_ACCOUNT")
    vpn_password = os.environ.get("VPN_PASSWORD")

    if not all([vpn_url, vpn_account, vpn_password]):
        print("❌ Missing VPN credentials.")
        sys.exit(1)

    print("🛡️ Bootstrapping EasyConnect macOS daemon...")
    try:
        subprocess.run(["open", "-a", "EasyConnect"], check=False)
        time.sleep(3)
    except:
        pass

    print(f"🧹 Launching Native System Safari to bypass Sangfor Kernel Routing Blocks...")
    
    applescript_open = f'''
    tell application "Safari"
        activate
        set fullTarget to "{vpn_url}"
        
        if (count of windows) = 0 then
            make new document with properties {{URL:fullTarget}}
        else
            -- V4: User explicitly requested to just pin/recycle a fixed tab
            -- We just ruthlessly assume "Tab 1 of Window 1" is the designated VPN tab
            set targetTab to tab 1 of front window
            
            -- Optional optimization: Only refresh if it's not already on the portal.
            set currentUrl to URL of targetTab as string
            if currentUrl does not contain "210.42.72.77" then
                set URL of targetTab to fullTarget
            end if
            set current tab of front window to targetTab
        end if
    end tell
    '''
    try:
        run_applescript(applescript_open)
    except Exception as e:
        print(f"❌ Failed to open Safari: {e}")
        sys.exit(1)

    print("⏳ Waiting for Sangfor Avalon.js to load in Safari...")
    time.sleep(5)
    
    js_payload = f'''
    (function() {{
        try {{
            let account = document.querySelector('input[type="text"][tabindex="1"]');
            let pwd = document.querySelector('input[type="password"][tabindex="2"], #loginPwd');
            if (!account || !pwd) return "FORM_NOT_FOUND";
            
            // Bypass Avalon.js Reactivity
            let nativeSet = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
            
            let triggerEvents = (el) => {{
                el.dispatchEvent(new Event('focus', {{bubbles: true}}));
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                el.dispatchEvent(new Event('blur', {{bubbles: true}}));
            }};
            
            nativeSet.call(account, '{vpn_account}');
            triggerEvents(account);
            
            nativeSet.call(pwd, '{vpn_password}');
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
    tell application "Safari"
        set js_result to do JavaScript "{js_payload_escaped}" in document 1
        return js_result
    end tell
    '''
    
    print("💻 Polling for login form and injecting credentials natively...")
    login_success = False
    for attempt in range(15): 
        try:
            result = run_applescript(applescript_inject)
            if "SUCCESS" in result:
                print("✅ Credentials injected and login clicked successfully!")
                login_success = True
                break
            elif "JS_ERROR" in result:
                print(f"⚠️ JavaScript Error: {result}")
        except Exception as e:
            if "AppleEvent" in str(e) or "JavaScript" in str(e):
                print("🚨 CRITICAL ERROR: Safari is blocking AppleScript JavaScript.")
                sys.exit(1)
        time.sleep(2)
            
    if not login_success:
        print("❌ Failed to find login form after 40 seconds. Check if Safari loaded the page correctly.")
        
    print("⏳ Waiting 15 seconds for dashboard to load and ECAgent to negotiate routing...")
    time.sleep(15)
    
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
            let first = document.querySelector('.resource-item, .app-item');
            if (first) {
                first.click();
                return "CLICKED_FALLBACK";
            }
            return "NO_RESOURCE_FOUND";
        } catch (err) {
            return "JS_ERROR:" + err.toString();
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
    
    tunnel_success = False
    for attempt in range(15):
        try:
            tunnel_result = run_applescript(applescript_tunnel)
            if "CLICKED" in tunnel_result:
                print(f"✅ Tunnel Trigger executed: {tunnel_result}")
                tunnel_success = True
                break
        except Exception as e:
            pass
        time.sleep(2)

    print("🎉 VPN sequence complete! Hiding Safari from view...")
    try:
        run_applescript('tell application "System Events" to set visible of process "Safari" to false')
    except:
        pass

    print("💓 Injecting HTTP Keep-Alive Daemon...")
    session = requests.Session()
    session.verify = False
    
    while True:
        time.sleep(300)
        try:
            session.head("https://210.42.72.77", verify=False, timeout=5)
            print("💓 Pulse Sent.", flush=True)
        except Exception:
            pass

if __name__ == "__main__":
    main()
