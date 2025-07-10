import time, sys
import numpy as np, cv2, mss
import pyautogui, pygetwindow as gw

REMOTE_ID = "1394620449"
ANYDESK_LAUNCH_WAIT = 3
CONNECTION_TIMEOUT  = 180
LOOK_INTERVAL       = 0.5

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.25

TEMPLATE = cv2.imread("disconnect_btn.png", cv2.IMREAD_GRAYSCALE)  # red ❌

# ----------------------------------------------------------------------
def launch_anydesk():
    pyautogui.press("win")
    time.sleep(0.8)
    pyautogui.write("anydesk", interval=0.05)
    pyautogui.press("enter")

def get_home_window():
    return next((w for w in gw.getWindowsWithTitle("AnyDesk") if w.visible), None)

def dial_id(win):
    pyautogui.click(win.left + 150, win.top + 85)
    pyautogui.write(REMOTE_ID, interval=0.05)
    pyautogui.press("enter")
    print("☎️  Dialling…")

# ----------------------------------------------------------------------
def match_toolbar_icon(threshold=0.85):
    if TEMPLATE is None:
        return False
    with mss.mss() as sct:
        frame = np.array(sct.grab(sct.monitors[1]))        # BGRA
    gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
    res  = cv2.matchTemplate(gray, TEMPLATE, cv2.TM_CCOEFF_NORMED)
    return (res >= threshold).any()

def wait_for_session(timeout=CONNECTION_TIMEOUT):
    print(f"⏳ Waiting (max {timeout}s) for remote user to accept…")
    start = time.time()
    while time.time() - start < timeout:
        # 1) Viewer window appears
        viewer = next(
            (w for w in gw.getAllTitles()
             if w.endswith(" - AnyDesk") and not w.lower().startswith("anydesk")),
            None
        )
        if viewer:
            print(f"✅ Session window: {viewer}")
            return True

        # 2) Toolbar icon visible
        if match_toolbar_icon():
            print("✅ Toolbar detected — session live.")
            return True

        time.sleep(LOOK_INTERVAL)
    print("❌ Timed out.")
    return False

# ----------------------------------------------------------------------
def get_viewer_window():
    return next(
        (w for w in gw.getWindowsWithTitle(" - AnyDesk") if w.visible and
         not w.title.lower().startswith("anydesk")), None)

def focus_remote_desktop(viewer):
    viewer.activate()
    time.sleep(0.4)
    # click once near the centre so the remote OS gains focus
    pyautogui.click(viewer.left + viewer.width // 2,
                    viewer.top  + viewer.height // 2)
    time.sleep(0.3)

def remote_tasks():
    """
    Example: open Run → %appdata%
    Requires AnyDesk 'Transmit Win key' enabled.
    """
    pyautogui.hotkey("win", "r")          # goes to remote now
    time.sleep(0.6)
    pyautogui.write("%appdata%", interval=0.05)
    pyautogui.press("enter")

# ----------------------------------------------------------------------
def main():
    launch_anydesk()
    time.sleep(ANYDESK_LAUNCH_WAIT)

    home = get_home_window()
    if not home:
        sys.exit("❌ AnyDesk home window not found.")
    home.activate(); time.sleep(0.3)
    dial_id(home)

    if not wait_for_session():
        sys.exit("Aborting — no session.")

    viewer = get_viewer_window()
    if not viewer:
        sys.exit("❌ Viewer window not found.")

    focus_remote_desktop(viewer)
    # Wait for toolbar icon to appear, up to 30 seconds
    print("⏳ Waiting for remote desktop toolbar icon to appear (max 30s)...")
    toolbar_timeout = 30
    toolbar_start = time.time()
    while time.time() - toolbar_start < toolbar_timeout:
        if match_toolbar_icon():
            print("✅ Toolbar icon detected. Remote desktop is ready.")
            break
        time.sleep(1)
    else:
        print("⚠️  Toolbar icon not detected after 30s. Proceeding anyway.")

    remote_tasks()
    print("🏁 Remote automation finished.")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Aborted by user.")
