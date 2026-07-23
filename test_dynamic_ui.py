import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(15000)
        
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
            
        print("Clicking on a project...")
        project_links = await page.query_selector_all("text='View Project'")
        if project_links:
            await project_links[0].click()
            await asyncio.sleep(2)
            
            print("Clicking on a document...")
            doc_links = await page.query_selector_all("text='test_invoice.pdf'")
            if doc_links:
                await doc_links[0].click()
                await asyncio.sleep(4)
                
                print("Taking screenshot...")
                await page.screenshot(path="C:/Users/HP/.gemini/antigravity-ide/brain/fa6c19fb-8977-44e5-9c5d-9aefeb83462c/dynamic_ui.png", full_page=True)
                print("Screenshot saved.")
            else:
                print("No documents found.")
        else:
            print("No projects found.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
