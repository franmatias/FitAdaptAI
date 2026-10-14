import type { RutinaResponse } from '../src/types/workout';

export const routine: RutinaResponse = {
  modo: 'ia', calentamiento: 'Movilidad de hombros y cadera',
  ejercicios: [{ nombre: 'Sentadilla al aire', series: 3, repeticiones: '8-10',
    descanso_segundos: 60, rpe_sugerido: 'RPE 6', consejo_tecnico: 'Mantén los talones apoyados.' }],
  alternativa_rapida: 'Puente de glúteos', tiempo_total_estimado: 20,
};

export const success = () => ({ ok: true, json: async () => structuredClone(routine) });
