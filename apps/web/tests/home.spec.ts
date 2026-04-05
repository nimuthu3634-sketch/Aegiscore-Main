import { expect, test } from "@playwright/test";

test("loads the AegisCore dashboard shell", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "AegisCore" })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "In-Scope Security Activity" })
  ).toBeVisible();
});
