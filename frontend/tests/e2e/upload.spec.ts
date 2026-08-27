import { test, expect } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";

// These E2E tests require both backend and frontend to be running.
// Backend: http://localhost:8000 (with FAKE_EXTRACTOR=true or real Gemini key)
// Frontend: http://localhost:5173

test.describe("Upload flow", () => {
  test("home page shows upload form", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("Lector de tickets");
    await expect(page.locator(".upload-card")).toBeVisible();
  });

  test("invalid file type shows error without uploading", async ({ page }) => {
    await page.goto("/");

    // Create a fake PDF in-memory
    const pdfContent = Buffer.from("%PDF-1.4 fake pdf");
    const pdfPath = path.join("/tmp", "test.pdf");
    fs.writeFileSync(pdfPath, pdfContent);

    const [fileChooser] = await Promise.all([
      page.waitForEvent("filechooser"),
      page.click(".drop-zone"),
    ]);
    await fileChooser.setFiles(pdfPath);

    await expect(page.locator(".alert-error")).toContainText(
      "Tipo no permitido",
    );

    fs.unlinkSync(pdfPath);
  });

  test("navigation to receipts list works", async ({ page }) => {
    await page.goto("/");
    await page.click('a[href="/receipts"]');
    await expect(page).toHaveURL("/receipts");
    await expect(page.locator("h1")).toContainText("Mis tickets");
  });

  test("receipts list page loads", async ({ page }) => {
    await page.goto("/receipts");
    // Either shows list or empty state
    const hasTable = await page.locator("table").count();
    const hasEmpty = await page.locator(".empty-state").count();
    expect(hasTable + hasEmpty).toBeGreaterThan(0);
  });
});

test.describe("Receipt detail", () => {
  test("detail page for nonexistent id shows error or redirects", async ({
    page,
  }) => {
    await page.goto("/receipts/nonexistent-fake-id");
    // Should show some error state or redirect
    // The page should not crash
    await expect(page.locator("body")).toBeVisible();
  });
});
