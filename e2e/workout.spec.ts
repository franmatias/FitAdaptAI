import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { routine } from '../tests/fixtures';

test.beforeEach(async ({ page }) => {
  // Si el frontend añade accidentalmente un servicio externo, no llegará a él.
  await page.route(/^https?:\/\/(?!127\.0\.0\.1(?::|\/))/, route => route.abort());
  await page.goto('/');
});

test('recorrido completo contra FastAPI real y resultado sin desbordamiento', async ({ page, request }) => {
  const health = await request.get('/api/health');
  expect(await health.json()).toMatchObject({ status: 'ok', modo: 'demo' });
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.getByRole('combobox', { name: 'Objetivo Principal' }).selectOption('fuerza');
  await page.getByRole('combobox', { name: 'Nivel de Experiencia' }).selectOption('principiante');
  await page.getByRole('slider').fill('20');
  await page.getByRole('button', { name: 'Peso Corporal', exact: true }).click();
  await page.getByRole('button', { name: 'Mancuernas', exact: true }).click();
  await page.getByRole('button', { name: 'Máquinas', exact: true }).click();
  const responsePromise = page.waitForResponse('**/api/generate-routine');
  await page.getByRole('button', { name: 'Generar mi rutina' }).click();
  const response = await responsePromise;
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.modo).toBe('demo');
  expect(data.tiempo_total_estimado).toBeLessThanOrEqual(20);
  const article = page.getByRole('article');
  await expect(article).toContainText('Demostración local');
  await expect(article.getByRole('heading', { level: 4 })).toHaveCount(4);
  for (const exercise of data.ejercicios) await expect(article).toContainText(exercise.nombre);
  await expect(article).toContainText(data.calentamiento);
  await expect(article).toContainText(data.alternativa_rapida);
  await page.getByRole('combobox', { name: 'Objetivo Principal' }).selectOption('resistencia');
  await expect(article).toContainText('Objetivo: fuerza');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
});

test('conserva al menos un equipo y permite manejarlo con teclado', async ({ page }) => {
  const dumbbells = page.getByRole('button', { name: 'Mancuernas', exact: true });
  const machines = page.getByRole('button', { name: 'Máquinas', exact: true });
  await dumbbells.focus();
  await page.keyboard.press('Space');
  await expect(dumbbells).toHaveAttribute('aria-pressed', 'false');
  await machines.focus();
  await page.keyboard.press('Enter');
  await expect(machines).toHaveAttribute('aria-pressed', 'true');
  const slider = page.getByRole('slider');
  await slider.focus();
  await page.keyboard.press('Home');
  await expect(slider).toHaveValue('20');
  await page.keyboard.press('End');
  await expect(slider).toHaveValue('75');
});

test('muestra carga accesible y evita peticiones duplicadas', async ({ page }) => {
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  let requests = 0;
  await page.route('**/api/generate-routine', async route => {
    requests++;
    await gate;
    await route.fulfill({ json: routine });
  });
  await page.getByRole('button', { name: 'Generar mi rutina' }).click();
  try {
    await expect(page.getByRole('status')).toContainText('Preparando');
    await expect(page.getByRole('combobox').first()).toBeDisabled();
    await expect(page.getByRole('slider')).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Preparando tu entrenamiento...' })).toBeDisabled();
    await page.locator('form').evaluate(form => form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  } finally { release(); }
  await expect(page.getByRole('article')).toContainText('Rutina generada con IA');
  expect(requests).toBe(1);
});

test('un error retira el resultado anterior y permite reintentar', async ({ page }) => {
  let attempt = 0;
  await page.route('**/api/generate-routine', route => {
    attempt++;
    return attempt === 2
      ? route.fulfill({ status: 503, json: { detail: 'Proveedor temporalmente no disponible' } })
      : route.fulfill({ json: routine });
  });
  const submit = page.getByRole('button', { name: 'Generar mi rutina' });
  await submit.click();
  await expect(page.getByRole('article')).toBeVisible();
  await submit.click();
  await expect(page.getByRole('alert')).toContainText('Proveedor temporalmente no disponible');
  await expect(page.getByRole('article')).toHaveCount(0);
  await submit.click();
  await expect(page.getByRole('article')).toBeVisible();
  await expect(page.getByRole('alert')).toHaveCount(0);
});

test('gestiona la pérdida de conexión y recupera el formulario', async ({ page }) => {
  await page.route('**/api/generate-routine', route => route.abort('failed'));
  await page.getByRole('button', { name: 'Generar mi rutina' }).click();
  await expect(page.getByRole('alert')).toContainText('No se pudo conectar');
  await expect(page.getByRole('button', { name: 'Generar mi rutina' })).toBeEnabled();
});

test('el límite de espera funciona en el navegador sin esperar 55 segundos', async ({ page }) => {
  await page.clock.install();
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/api/generate-routine', async route => { await gate; await route.abort(); });
  await page.getByRole('button', { name: 'Generar mi rutina' }).click();
  await expect(page.getByRole('status')).toBeVisible();
  try {
    await page.clock.fastForward(55_001);
    await expect(page.getByRole('alert')).toContainText('ha tardado demasiado');
    await expect(page.getByRole('button', { name: 'Generar mi rutina' })).toBeEnabled();
  } finally { release(); }
});

test('sin infracciones automáticas WCAG A/AA en formulario, resultado y error', async ({ page }) => {
  const scan = async () => {
    const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
    expect(result.violations).toEqual([]);
  };
  await scan();
  await page.getByRole('button', { name: 'Generar mi rutina' }).click();
  await expect(page.getByRole('article')).toBeVisible();
  await scan();
  await page.route('**/api/generate-routine', route => route.fulfill({ status: 502, json: { detail: 'Inténtalo de nuevo' } }));
  await page.getByRole('button', { name: 'Generar mi rutina' }).click();
  await expect(page.getByRole('alert')).toBeVisible();
  await scan();
});
