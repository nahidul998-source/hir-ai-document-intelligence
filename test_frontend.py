import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(10000)
        
        print("Navigating to frontend...")
        await page.goto("http://localhost:5173")
        
        # Wait a bit for the page to load
        await asyncio.sleep(2)
        
        # Check if we need to login
        login_button = await page.query_selector("text='Sign In'")
        if login_button:
            print("Logging in...")
            await page.fill("input[type='email']", "admin@example.com")
            await page.fill("input[type='password']", "admin")
            await page.click("text='Sign In'")
            # Wait for dashboard to load
            await page.wait_for_selector("text='New Project'")
        
        print("Creating project...")
        await page.click("text='New Project'")
        
        await page.fill("input[placeholder='e.g. Autumn Techpacks']", "Test Project Playwright")
        await page.click("button:has-text('Create Project')")
        
        print("Waiting for file input...")
        # Wait a bit for state to settle
        await asyncio.sleep(2)
        
        # The file input should be present now
        await page.wait_for_selector("input[type='file']")
        
        print("Uploading file...")
        await page.set_input_files("input[type='file']", "e:/HIR-ai-document-intelligence/test_invoice.pdf")
        
        print("Waiting for upload and AI processing (10s)...")
        await asyncio.sleep(10)
        
        # Try to click on the uploaded document in the list if it appears
        try:
            await page.click("text='test_invoice.pdf'")
            print("Clicked on document, waiting 3s for viewer to load...")
            await asyncio.sleep(3)
        except Exception as e:
            print(f"Could not click document: {e}")
        
        print("Taking screenshot...")
        await page.screenshot(path="C:/Users/HP/.gemini/antigravity-ide/brain/fa6c19fb-8977-44e5-9c5d-9aefeb83462c/playwright_test_result.png", full_page=True)
        
        print("Test Complete.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
