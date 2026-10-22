import { test, expect, type Page } from "playwright/test";

const BRAND_ORANGE = "rgb(255, 85, 0)";
const BRAND_SURFACE = "rgb(255, 255, 255)";

const launcherSelector =
  'button[aria-label="Ouvrir le chat"], button[aria-label="Fermer le chat"]';

function chatPanel(page: Page) {
  return page.locator("textarea").locator("xpath=../..//..");
}

test.describe("Chat widget brand colors", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("launcher button is brand orange", async ({ page }) => {
    const launcher = page.locator(launcherSelector).first();
    await expect(launcher).toBeVisible();
    const background = await launcher.evaluate(
      (element) => getComputedStyle(element).backgroundColor
    );
    expect(background).toBe(BRAND_ORANGE);
  });

  test("chat panel background is brand surface", async ({ page }) => {
    await page.locator(launcherSelector).first().click();

    const panel = chatPanel(page);
    await expect(panel).toBeVisible();
    const background = await panel.evaluate(
      (element) => getComputedStyle(element).backgroundColor
    );
    expect(background).toBe(BRAND_SURFACE);
  });

  test("send button is brand orange", async ({ page }) => {
    await page.locator(launcherSelector).first().click();

    const sendButton = page.locator('button[aria-label="Envoyer"]');
    await expect(sendButton).toBeVisible();
    const background = await sendButton.evaluate(
      (element) => getComputedStyle(element).backgroundColor
    );
    expect(background).toBe(BRAND_ORANGE);
  });

  test("close button closes the panel", async ({ page }) => {
    await page.locator(launcherSelector).first().click();

    const textarea = page.locator("textarea");
    await expect(textarea).toBeVisible();
    await page.locator('button[aria-label="Fermer"]').click();
    await expect(textarea).not.toBeVisible();
  });

  test("no legacy neutral backgrounds on panel descendants", async ({
    page,
  }) => {
    await page.locator(launcherSelector).first().click();

    const panel = chatPanel(page);
    await expect(panel).toBeVisible();
    const legacyCount = await panel.evaluate((element) => {
      const nodes = [element, ...element.querySelectorAll("*")];
      return nodes.filter((node) => {
        const className =
          typeof node.className === "string" ? node.className : "";
        return /\bbg-neutral-900\b|\bbg-white\b/.test(className);
      }).length;
    });
    expect(legacyCount).toBeLessThanOrEqual(2);
  });
});
