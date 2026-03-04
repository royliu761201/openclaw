#!/bin/bash
# --------------------------------------------------------------------
# 📱 Android Edge Node "God-Mode" Auto Provisioner via ADB
# 使用前提: 
#   1. 手机连上 Mac/03机 的 USB 线。
#   2. 手机打开【开发者选项】-> 勾选【USB 调试】。
#   3. 当前目录下要有 Termux_Main.apk, Termux_API.apk, 和 Tailscale.apk 这三个包。
# --------------------------------------------------------------------

echo "🔌 等待设备连接 (请留意手机屏幕，若弹出 USB 调试授权请点【始终允许】)..."
adb wait-for-device

echo "📦 [1/5] 正在底层越权静默安装【大脑】(Termux 主程序)..."
adb install -r -g Termux_Main.apk

echo "📦 [2/5] 正在底层越权静默安装【手脚】(Termux:API 硬件桥接器)..."
adb install -r -g Termux_API.apk

echo "📦 [3/5] 正在底层越权静默安装【网络专线】(Tailscale)..."
adb install -r -g Tailscale.apk

echo "🔐 [4/5] 正在用 ADB Root 级权限强行打通全部物理器官授权 (免弹窗、免点击)..."
adb shell pm grant com.termux.api android.permission.CAMERA
adb shell pm grant com.termux.api android.permission.RECORD_AUDIO
adb shell pm grant com.termux.api android.permission.ACCESS_FINE_LOCATION
adb shell pm grant com.termux.api android.permission.READ_CONTACTS
adb shell pm grant com.termux.api android.permission.READ_CALL_LOG
adb shell pm grant com.termux.api android.permission.READ_SMS

echo "🔋 [5/5] 正在注入休眠白名单防断连，并唤醒所有后台进程..."
adb shell dumpsys deviceidle whitelist +com.termux >/dev/null 2>&1
adb shell dumpsys deviceidle whitelist +com.termux.api >/dev/null 2>&1
adb shell dumpsys deviceidle whitelist +com.tailscale.ipn >/dev/null 2>&1

# 唤醒一次 API 激活硬件总线
adb shell monkey -p com.termux.api -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
sleep 1

# 唤醒 Tailscale 界面让老板登录
echo "🌐 正在弹出 Tailscale，请在手机上点击 Log In 进行登录并授权 VPN..."
adb shell monkey -p com.tailscale.ipn -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
sleep 2

# 唤出主屏幕黑框
adb shell monkey -p com.termux -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1

echo "========================================================================"
echo "✅ 恭喜老板！物理层面全部搞定！"
echo "您现在连手机屏幕都不用碰一下，所有的包（含 Tailscale）全装好，硬件权限全点亮了！"
echo "请在屏幕上登录 Tailscale 后，回到 Mac 上连接，并执行网络端那个 termux_bootstrap.sh 即可！"
echo "========================================================================"
