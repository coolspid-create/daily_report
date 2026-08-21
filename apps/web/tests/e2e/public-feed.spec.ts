import { expect, test } from "@playwright/test";

test("topic and range change on the same public page", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /오늘의\s*공공리포트/ })).toBeVisible();
  await expect(page.locator("main")).toHaveAttribute("data-hydrated", "true");
  await page.getByRole("button", { name: "법·외교·안보" }).click();
  await expect(page).toHaveURL(/topic=law-security/);
  await expect(page.getByText("「자살예방법」은 무엇을 놓치고 있는가")).toBeVisible();
  await page.reload();
  await expect(page.getByRole("button", { name: "법·외교·안보" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByText("최근 7일 꼭 볼 자료")).toBeVisible();
});

test("admin route is protected", async ({ page }) => {
  await page.goto("/admin");
  await expect(page).toHaveURL(/\/admin\/login/);
  await expect(page.getByRole("heading", { name: "관리자 로그인" })).toBeVisible();
});
