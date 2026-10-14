import { mount, flushPromises } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import App from '../src/App.vue';
import { routine, success } from './fixtures';

describe('Contrato y estados de la sesión', () => {
  it('envía los cuatro parámetros editados con los tipos y cabeceras correctos', async () => {
    const fetch = vi.fn().mockResolvedValue(success());
    vi.stubGlobal('fetch', fetch);
    const wrapper = mount(App);
    await wrapper.get('[aria-label="Objetivo Principal"]').setValue('resistencia');
    await wrapper.get('[aria-label="Nivel de Experiencia"]').setValue('principiante');
    await wrapper.get('input').setValue(20);
    const equipment = wrapper.findAll('button[aria-pressed]');
    await equipment[4].trigger('click');
    await equipment[0].trigger('click');
    await equipment[1].trigger('click');
    await wrapper.get('form').trigger('submit');
    await flushPromises();
    expect(fetch).toHaveBeenCalledOnce();
    const [url, options] = fetch.mock.calls[0];
    expect(url).toBe('/api/generate-routine');
    expect(options.method).toBe('POST');
    expect(options.headers).toEqual({ 'Content-Type': 'application/json' });
    expect(JSON.parse(options.body)).toEqual({ objetivo: 'resistencia', nivel: 'principiante',
      tiempo_minutos: 20, equipamiento: ['peso_corporal'] });
    const result = wrapper.get('article').text();
    for (const value of [routine.calentamiento, routine.ejercicios[0].nombre, '8-10', '60s',
      'RPE 6', routine.ejercicios[0].consejo_tecnico, routine.alternativa_rapida, '20 min', 'Rutina generada con IA']) {
      expect(result).toContain(value);
    }
  });

  it('ignora envíos repetidos mientras hay una petición pendiente y limpia el temporizador', async () => {
    vi.useFakeTimers();
    let resolve!: (value: unknown) => void;
    const fetch = vi.fn(() => new Promise(r => { resolve = r; }));
    vi.stubGlobal('fetch', fetch);
    const wrapper = mount(App);
    await wrapper.get('form').trigger('submit');
    await wrapper.get('form').trigger('submit');
    expect(fetch).toHaveBeenCalledOnce();
    expect(wrapper.get('form').attributes('aria-busy')).toBe('true');
    expect(wrapper.get('[role="status"]').text()).toContain('Preparando');
    resolve(success());
    await flushPromises();
    expect(wrapper.get('form').attributes('aria-busy')).toBe('false');
    expect(wrapper.find('[role="status"]').exists()).toBe(false);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('aborta tras 55 segundos y permite una nueva generación', async () => {
    vi.useFakeTimers();
    const fetch = vi.fn().mockImplementationOnce((_url, { signal }: RequestInit) => new Promise((_resolve, reject) => {
      signal!.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')));
    })).mockResolvedValueOnce(success());
    vi.stubGlobal('fetch', fetch);
    const wrapper = mount(App);
    await wrapper.get('form').trigger('submit');
    await vi.advanceTimersByTimeAsync(55000);
    await flushPromises();
    expect(wrapper.get('[role="alert"]').text()).toContain('ha tardado demasiado');
    expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeUndefined();
    await wrapper.get('form').trigger('submit');
    await flushPromises();
    expect(wrapper.find('[role="alert"]').exists()).toBe(false);
    expect(wrapper.find('article').exists()).toBe(true);
    expect(vi.getTimerCount()).toBe(0);
  });

  it.each([
    [new TypeError('Failed to fetch'), 'No se pudo conectar'],
    [new Error('Servicio no disponible'), 'Servicio no disponible'],
    ['unknown', 'Ocurrió un error inesperado'],
  ])('presenta un error legible y recupera los controles: %s', async (error, message) => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(error));
    const wrapper = mount(App);
    await wrapper.get('form').trigger('submit');
    await flushPromises();
    expect(wrapper.get('[role="alert"]').text()).toContain(message);
    expect(wrapper.find('article').exists()).toBe(false);
    expect(wrapper.get('fieldset').attributes('disabled')).toBeUndefined();
  });

  it('tolera una página de error HTML en lugar de JSON', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, json: async () => { throw new SyntaxError('HTML'); } }));
    const wrapper = mount(App);
    await wrapper.get('form').trigger('submit');
    await flushPromises();
    expect(wrapper.get('[role="alert"]').text()).toContain('Revisa los datos');
  });

  it('rechaza una duración manipulada sin llamar al servidor', async () => {
    const fetch = vi.fn();
    vi.stubGlobal('fetch', fetch);
    const wrapper = mount(App);
    const slider = wrapper.get('input');
    // Quita las restricciones nativas para simular una manipulación desde el navegador.
    slider.element.setAttribute('type', 'number');
    await slider.setValue(21);
    await wrapper.get('form').trigger('submit');
    expect(fetch).not.toHaveBeenCalled();
    expect(wrapper.get('[role="alert"]').text()).toContain('Revisa la duración');
  });

  it('renderiza contenido del proveedor como texto, sin ejecutar HTML', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({
      ...routine, calentamiento: '<img src=x onerror="alert(1)">',
    }) }));
    const wrapper = mount(App);
    await wrapper.get('form').trigger('submit');
    await flushPromises();
    expect(wrapper.get('article').text()).toContain('<img src=x');
    expect(wrapper.find('article img').exists()).toBe(false);
  });
});
