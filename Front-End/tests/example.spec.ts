import { test, expect } from '@playwright/test';

test.describe('Chat Page E2E Test', () => {
  test('should allow users to send a message and receive a bot response', async ({ page }) => {

    await page.goto('http://localhost:4200/chat');

    const userInputSelector = 'input';
    const sendButtonSelector = 'button:has-text("Send")';
    const messagesContainerSelector = '.message-content';

    const userMessage = 'What is used for backend?';
    await page.fill(userInputSelector, userMessage);

    await page.click(sendButtonSelector);

    await page.waitForSelector(`.bot-reply .message-content`, {
      state: 'visible',
      timeout: 20000,
    });

    const messages = await page.$$(`.message`);

    const userMessageText = await messages[0].textContent();
    expect(userMessageText).toContain(userMessage);

    const botMessageText = await messages[1].textContent();

    console.log(botMessageText)

    expect(botMessageText).not.toContain('Failed');
    expect(botMessageText).toContain('Flask');
    expect(botMessageText).toBeTruthy();
  });
});
