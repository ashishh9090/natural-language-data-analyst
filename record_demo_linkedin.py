"""
Automated recording script for LinkedIn demo.
Controls Chrome via CDP while recording screen via macOS screencapture.
"""

import asyncio
import json
import os
import subprocess
import time
import urllib.request
import websockets

OUTPUT_FILE = "/Users/apple/.gemini/antigravity-ide/scratch/nl-data-analyst/demo_natural_language_data_analyst.mp4"
RECORD_SECONDS = 25


async def run_cdp(ws, method, params=None):
    if params is None:
        params = {}
    msg_id = int(time.time() * 1000) % 1000000
    payload = {"id": msg_id, "method": method, "params": params}
    await ws.send(json.dumps(payload))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == msg_id:
            return resp


async def eval_js(ws, expr):
    res = await run_cdp(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True})
    return res.get("result", {}).get("result", {}).get("value")


async def main():
    print("1. Activating and positioning Google Chrome...")
    subprocess.run([
        "osascript", "-e",
        'tell application "Google Chrome" to activate'
    ], check=False)
    await asyncio.sleep(1)

    print("2. Connecting to Chrome via CDP...")
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read())
    target = None
    for p in pages:
        if p.get("type") == "page" and "8502" in p.get("url", ""):
            target = p
            break
    if not target:
        for p in pages:
            if p.get("type") == "page":
                target = p
                break

    if not target:
        print("No target page found! Creating new page...")
        req = urllib.request.urlopen("http://127.0.0.1:9222/json/new?http://localhost:8502")
        target = json.loads(req.read())

    ws_url = target["webSocketDebuggerUrl"]
    print(f"Connecting to: {ws_url}")

    # Remove previous recording if exists
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    print(f"3. Starting screen recording for {RECORD_SECONDS} seconds...")
    rec_proc = subprocess.Popen([
        "screencapture", "-V", str(RECORD_SECONDS), OUTPUT_FILE
    ])

    async with websockets.connect(ws_url) as ws:
        # Step 0: Ensure page is at top
        await eval_js(ws, "window.scrollTo(0, 0);")
        await asyncio.sleep(2)

        # Step 1: Click "Load Sample E-Commerce Data"
        print("4. Clicking 'Load Sample E-Commerce Data'...")
        click_sample_js = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const b = btns.find(x => x.innerText && x.innerText.includes('Load Sample'));
            if (b) { b.click(); return true; }
            return false;
        })()
        """
        await eval_js(ws, click_sample_js)
        await asyncio.sleep(3)

        # Step 2: Expand Dataset Overview
        print("5. Expanding Dataset Overview...")
        expand_js = """
        (() => {
            const expander = document.querySelector('[data-testid="stExpander"]');
            if (expander) {
                const summary = expander.querySelector('summary') || expander;
                summary.click();
                return true;
            }
            return false;
        })()
        """
        await eval_js(ws, expand_js)
        await asyncio.sleep(3.5)

        # Step 3: Click suggested question chip (Highest revenue)
        print("6. Selecting question: 'Which product had the highest revenue?'...")
        click_chip_js = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const chip = btns.find(x => x.innerText && (x.innerText.includes('highest revenue') || x.innerText.includes('Highest Revenue')));
            if (chip) { chip.click(); return true; }
            return false;
        })()
        """
        await eval_js(ws, click_chip_js)
        await asyncio.sleep(2)

        # Step 4: Click 'Analyze Data'
        print("7. Submitting analysis...")
        submit_js = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const b = btns.find(x => x.innerText && x.innerText.includes('Analyze Data'));
            if (b) { b.click(); return true; }
            return false;
        })()
        """
        await eval_js(ws, submit_js)
        await asyncio.sleep(3.5)

        # Step 5: Smooth scroll down to direct answer card & chart
        print("8. Scrolling to results and Plotly chart...")
        await eval_js(ws, "window.scrollTo({ top: 480, behavior: 'smooth' });")
        await asyncio.sleep(3.5)

        # Step 6: Scroll further to method, disclaimers, and data table
        print("9. Scrolling to method explanation and data records...")
        await eval_js(ws, "window.scrollTo({ top: 820, behavior: 'smooth' });")
        await asyncio.sleep(3.5)

        # Step 7: Scroll smoothly back to top for final overview
        print("10. Smooth scroll back up...")
        await eval_js(ws, "window.scrollTo({ top: 200, behavior: 'smooth' });")
        await asyncio.sleep(2)

    print("11. Waiting for screencapture process to complete...")
    rec_proc.wait()
    print("Recording finished!")

    if os.path.exists(OUTPUT_FILE):
        size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
        print(f"SUCCESS: Video saved to {OUTPUT_FILE} ({size_mb:.2f} MB)")
    else:
        print("ERROR: Output file was not created.")


if __name__ == "__main__":
    asyncio.run(main())
