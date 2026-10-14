import { mount, flushPromises } from '@vue/test-utils';
import { afterEach, expect, it, vi } from 'vitest';
import App from '../src/App.vue';

afterEach(() => vi.unstubAllGlobals());

it('mantiene al menos un equipo seleccionado', async () => {
  const wrapper = mount(App);
  const selected = wrapper.findAll('button[aria-pressed="true"]');
  await selected[0].trigger('click');
  await selected[1].trigger('click');
  expect(wrapper.findAll('button[aria-pressed="true"]')).toHaveLength(1);
  wrapper.unmount();
});

it('bloquea el formulario, muestra el error y permite reintentar', async () => {
  let resolve!: (value: unknown) => void;
  vi.stubGlobal('fetch', vi.fn(() => new Promise(r => { resolve = r; })));
  const wrapper = mount(App);
  await wrapper.find('form').trigger('submit');
  expect(wrapper.find('fieldset').attributes()).toHaveProperty('disabled');
  expect(wrapper.find('button[type="submit"]').attributes()).toHaveProperty('disabled');
  resolve({ ok: false, json: async () => ({ detail: 'Proveedor no disponible' }) });
  await flushPromises();
  expect(wrapper.find('[role="alert"]').text()).toContain('Proveedor no disponible');
  expect(wrapper.find('fieldset').attributes()).not.toHaveProperty('disabled');
  wrapper.unmount();
});

it('muestra un mensaje legible para errores de validación del servidor', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, json: async () => ({ detail: [{ msg: 'error' }] }) }));
  const wrapper = mount(App);
  await wrapper.find('form').trigger('submit');
  await flushPromises();
  expect(wrapper.find('[role="alert"]').text()).toContain('Revisa los datos');
  wrapper.unmount();
});

it('conserva los parámetros de la sesión generada al editar el formulario', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({
    calentamiento: 'Movilidad', ejercicios: [], alternativa_rapida: 'Alternativa', tiempo_total_estimado: 25, modo: 'demo',
  }) }));
  const wrapper = mount(App);
  await wrapper.find('form').trigger('submit');
  await flushPromises();
  await wrapper.find('select[aria-label="Objetivo Principal"]').setValue('fuerza');
  expect(wrapper.find('article').text()).toContain('hipertrofia');
  expect(wrapper.find('article').text()).toContain('Demostración local');
  wrapper.unmount();
});

it('retira una rutina anterior cuando falla una nueva generación', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({
      calentamiento: 'Movilidad', ejercicios: [], alternativa_rapida: 'Alternativa', tiempo_total_estimado: 25, modo: 'demo',
    }) })
    .mockResolvedValueOnce({ ok: false, json: async () => ({ detail: 'Proveedor no disponible' }) });
  vi.stubGlobal('fetch', fetchMock);
  const wrapper = mount(App);
  await wrapper.find('form').trigger('submit');
  await flushPromises();
  expect(wrapper.find('article').exists()).toBe(true);
  await wrapper.find('form').trigger('submit');
  await flushPromises();
  expect(wrapper.find('article').exists()).toBe(false);
  expect(wrapper.find('[role="alert"]').text()).toContain('Proveedor no disponible');
  wrapper.unmount();
});
