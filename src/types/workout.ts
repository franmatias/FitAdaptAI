export type Objetivo = 'hipertrofia' | 'fuerza' | 'perdida_grasa' | 'resistencia';
export type Nivel = 'principiante' | 'intermedio' | 'avanzado';
export type Equipamiento = 'mancuernas' | 'maquinas' | 'poleas' | 'barras_discos' | 'peso_corporal';

export interface WorkoutRequest {
  objetivo: Objetivo;
  tiempo_minutos: number;
  equipamiento: Equipamiento[];
  nivel: Nivel;
}

export interface Ejercicio {
  nombre: string;
  series: number;
  repeticiones: string;
  descanso_segundos: number;
  rpe_sugerido: string;
  consejo_tecnico: string;
}

export interface RutinaResponse {
  modo?: 'demo' | 'ia';
  calentamiento: string;
  ejercicios: Ejercicio[];
  alternativa_rapida: string;
  tiempo_total_estimado: number;
}
