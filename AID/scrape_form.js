const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://wvixbzgc0u7.feishu.cn/share/base/form/shrcnI5EfY5oo8OSn05CEbHEqac', { waitUntil: 'networkidle' });
  
  // Close any popups
  try {
    await page.click('text=我知道了', { timeout: 3000 });
  } catch(e) {}
  
  await page.waitForTimeout(2000);
  
  // Get all form field labels
  const content = await page.evaluate(() => {
    const labels = document.querySelectorAll('[class*="label"], [class*="title"], h1, h2, h3, h4, span, p, div');
    const texts = new Set();
    labels.forEach(el => {
      const text = el.textContent?.trim();
      if (text && text.length > 2 && text.length < 200) {
        texts.add(text);
      }
    });
    return Array.from(texts).join('\n---\n');
  });
  
  console.log('=== FORM CONTENT ===');
  console.log(content);
  
  // Also get the full page text
  const fullText = await page.evaluate(() => document.body.innerText);
  console.log('\n=== FULL PAGE TEXT ===');
  console.log(fullText);
  
  await browser.close();
})();
