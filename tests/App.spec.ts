import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../src/App.vue';
import type { RutinaResponse } from '../src/types/workout';

describe('FitAdapt Vue 3 Frontend Component Tests', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renderiza correctamente el formulario y sus 4 campos principales', () => {
    const wrapper = mount(App);

    expect(wrapper.text()).toContain('1. Objetivo Principal');
    expect(wrapper.text()).toContain('2. Duración de la Sesión');
    expect(wrapper.text()).toContain('3. Nivel de Experiencia');
    expect(wrapper.text()).toContain('4. Equipamiento Disponible');
    expect(wrapper.find('button[type="submit"]').text()).toContain('Generar mi rutina');
  });

  it('procesa el envío del formulario y renderiza los datos devueltos por la API', async () => {
    const mockRutina: RutinaResponse = {
      calentamiento: 'Rotaciones de tobillo y 5 minutos de trote suave.',
      ejercicios: [
        {
          nombre: 'Sentadilla Goblet con Mancuerna',
          series: 3,
          repeticiones: '10-12',
          descanso_segundos: 60,
          rpe_sugerido: 'RPE 7.5',
          consejo_tecnico: 'Mantén los talones firmes en el suelo y el pecho erguido.',
        },
      ],
      alternativa_rapida: 'Zancadas estáticas si la mancuerna pesada está en uso.',
      tiempo_total_estimado: 45,
    };

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockRutina,
    }));

    const wrapper = mount(App);

    // Disparar el evento de submit del formulario
    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    // Verificar que los datos mockeados se han renderizado en el DOM
    expect(wrapper.text()).toContain('Tu Sesión Personalizada');
    expect(wrapper.text()).toContain('Sentadilla Goblet con Mancuerna');
    expect(wrapper.text()).toContain('Rotaciones de tobillo y 5 minutos de trote suave.');
    expect(wrapper.text()).toContain('Zancadas estáticas si la mancuerna pesada está en uso.');
  });
});
