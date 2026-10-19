<script setup lang="ts">
import { ref } from 'vue';
import {
  Dumbbell,
  Clock,
  Target,
  Award,
  Loader2,
  Sparkles,
  AlertCircle,
  CheckCircle2,
} from 'lucide-vue-next';
import type {
  Objetivo,
  Nivel,
  Equipamiento,
  WorkoutRequest,
  RutinaResponse,
} from './types/workout';

const props = defineProps<{
  getToken?: () => Promise<string | null>;
}>();

interface EquipamientoOpcion {
  id: Equipamiento;
  label: string;
}

const OPCIONES_EQUIPAMIENTO: EquipamientoOpcion[] = [
  { id: 'mancuernas', label: 'Mancuernas' },
  { id: 'maquinas', label: 'Máquinas' },
  { id: 'poleas', label: 'Poleas' },
  { id: 'barras_discos', label: 'Barras y Discos' },
  { id: 'peso_corporal', label: 'Peso Corporal' },
];

// Estado Reactivo
const objetivo = ref<Objetivo>('hipertrofia');
const tiempoMinutos = ref<number>(45);
const equipamiento = ref<Equipamiento[]>(['mancuernas', 'maquinas']);
const nivel = ref<Nivel>('intermedio');

const generatedFor = ref<WorkoutRequest | null>(null);
const loading = ref<boolean>(false);
const error = ref<string | null>(null);
const rutina = ref<RutinaResponse | null>(null);

const toggleEquipamiento = (id: Equipamiento): void => {
  if (equipamiento.value.includes(id)) {
    if (equipamiento.value.length > 1) {
      equipamiento.value = equipamiento.value.filter((item) => item !== id);
    }
  } else {
    equipamiento.value.push(id);
  }
};

const handleSubmit = async (): Promise<void> => {
  if (loading.value) return;
  if (!Number.isInteger(tiempoMinutos.value) || tiempoMinutos.value < 20 || tiempoMinutos.value > 75 || tiempoMinutos.value % 5 !== 0 || !equipamiento.value.length) {
    error.value = 'Revisa la duración y selecciona al menos un equipamiento.';
    return;
  }
  loading.value = true;
  error.value = null;
  rutina.value = null;
  generatedFor.value = null;

  const payload: WorkoutRequest = {
    objetivo: objetivo.value,
    tiempo_minutos: Number(tiempoMinutos.value),
    equipamiento: [...equipamiento.value],
    nivel: nivel.value,
  };

  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 55000);
  try {
    const token = await props.getToken?.();
    if (props.getToken && !token) {
      throw new Error('Tu sesión ha caducado. Inicia sesión de nuevo para continuar.');
    }
    const response = await fetch('/api/generate-routine', {
      method: 'POST',
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(typeof errorData.detail === 'string' ? errorData.detail : 'Revisa los datos del formulario y vuelve a intentarlo.');
    }

    const data: RutinaResponse = await response.json();
    rutina.value = data;
    generatedFor.value = payload;
  } catch (err: unknown) {
    if (err instanceof Error || err instanceof DOMException) {
      error.value = err.name === 'AbortError' ? 'La petición ha tardado demasiado. Vuelve a intentarlo.' : err instanceof TypeError ? 'No se pudo conectar. Comprueba que el servidor local está en marcha.' : err.message;
    } else {
      error.value = 'Ocurrió un error inesperado.';
    }
  } finally {
    window.clearTimeout(timeout);
    loading.value = false;
  }
};
</script>

<template>
  <main class="min-h-screen bg-slate-950 text-slate-100 py-10 px-4 sm:px-6 lg:px-8">
    <div class="max-w-4xl mx-auto space-y-8">
      
      <!-- Cabecera -->
      <header class="text-center space-y-2">
        <div class="inline-flex items-center justify-center p-3 bg-emerald-500/10 text-emerald-400 rounded-2xl mb-2 border border-emerald-500/20">
          <Dumbbell class="w-8 h-8" />
        </div>
        <h1 class="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
          Fit<span class="text-emerald-400">Adapt</span> AI
        </h1>
        <p class="text-slate-400 max-w-lg mx-auto text-sm sm:text-base">
          Tu objetivo. Tu tiempo. Tu entrenamiento.
          Diseña una sesión adaptada al material que tienes a mano.
        </p>
      </header>

      <div class="flex justify-center gap-3 text-xs text-slate-400"><span>01 · Configura</span><span aria-hidden="true">→</span><span>02 · Genera</span><span aria-hidden="true">→</span><span>03 · Entrena</span></div>
      <!-- Formulario de Entrada (4 datos) -->
      <section class="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl">
        <form @submit.prevent="handleSubmit" :aria-busy="loading">
          <fieldset :disabled="loading" class="space-y-6">
          <legend class="sr-only">Configura tu entrenamiento</legend>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            <!-- 1. Objetivo -->
            <div>
              <label class="flex items-center text-sm font-semibold text-slate-300 mb-2">
                <Target class="w-4 h-4 mr-2 text-emerald-400" />
                1. Objetivo Principal
              </label>
              <select
                v-model="objetivo"
                aria-label="Objetivo Principal"
                class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="hipertrofia">Hipertrofia (Masa Muscular)</option>
                <option value="fuerza">Fuerza Pura</option>
                <option value="perdida_grasa">Pérdida de Grasa / Definición</option>
                <option value="resistencia">Resistencia Muscular</option>
              </select>
            </div>

            <!-- 2. Tiempo disponible -->
            <div>
              <div class="flex justify-between items-center mb-2">
                <label class="flex items-center text-sm font-semibold text-slate-300">
                  <Clock class="w-4 h-4 mr-2 text-emerald-400" />
                  2. Duración de la Sesión
                </label>
                <span class="text-xs font-bold px-2.5 py-1 bg-emerald-500/20 text-emerald-400 rounded-md">
                  {{ tiempoMinutos }} minutos
                </span>
              </div>
              <input
                v-model.number="tiempoMinutos"
                type="range"
                aria-label="Tiempo de Sesión"
                min="20"
                max="75"
                step="5"
                class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
              />
              <div class="flex justify-between text-xs text-slate-400 mt-1">
                <span>20m</span>
                <span>45m</span>
                <span>75m</span>
              </div>
            </div>

            <!-- 3. Nivel de Experiencia -->
            <div>
              <label class="flex items-center text-sm font-semibold text-slate-300 mb-2">
                <Award class="w-4 h-4 mr-2 text-emerald-400" />
                3. Nivel de Experiencia
              </label>
              <select
                v-model="nivel"
                aria-label="Nivel de Experiencia"
                class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="principiante">Principiante (&lt; 6 meses)</option>
                <option value="intermedio">Intermedio (6 meses a 2 años)</option>
                <option value="avanzado">Avanzado (&gt; 2 años)</option>
              </select>
            </div>

            <!-- 4. Equipamiento Disponible -->
            <div>
              <label class="flex items-center text-sm font-semibold text-slate-300 mb-2">
                <Dumbbell class="w-4 h-4 mr-2 text-emerald-400" />
                4. Equipamiento Disponible
              </label>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="opcion in OPCIONES_EQUIPAMIENTO"
                  :key="opcion.id"
                  :aria-pressed="equipamiento.includes(opcion.id)"
                  type="button"
                  @click="toggleEquipamiento(opcion.id)"
                  :class="[
                    'text-xs px-3 py-2 rounded-lg font-medium transition border',
                    equipamiento.includes(opcion.id)
                      ? 'bg-emerald-500 text-slate-950 border-emerald-400 font-semibold'
                      : 'bg-slate-800 text-slate-400 border-slate-700 hover:border-slate-600'
                  ]"
                >
                  {{ opcion.label }}
                </button>
              </div>
            </div>

          </div>

          <!-- Botón de Envío -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full flex items-center justify-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold py-3.5 px-6 rounded-xl transition duration-150 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-emerald-500/20"
          >
            <template v-if="loading">
              <Loader2 class="w-5 h-5 animate-spin" />
              <span>Preparando tu entrenamiento...</span>
            </template>
            <template v-else>
              <Sparkles class="w-5 h-5" />
              <span>Generar mi rutina</span>
            </template>
          </button>
          </fieldset>
        </form>
      </section>

      <!-- Alerta de Error -->
      <section
        v-if="error"
        role="alert"
        class="bg-rose-950/40 border border-rose-800 text-rose-300 p-4 rounded-xl flex items-start gap-3"
      >
        <AlertCircle class="w-5 h-5 text-rose-400 mt-0.5 flex-shrink-0" />
        <div>
          <h2 class="font-semibold text-rose-200 text-sm">Error en la petición</h2>
          <p class="text-sm">{{ error }}</p>
        </div>
      </section>

      <p v-if="loading" role="status" class="text-center text-emerald-300">Preparando tu sesión…</p>
      <!-- Resultado de la Rutina -->
      <article
        v-if="rutina"
        class="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6 shadow-2xl"
      >
        <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-2">
          <div>
            <h2 class="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
              <CheckCircle2 class="w-6 h-6 text-emerald-400" />
              Tu Sesión Personalizada
            </h2>
            <p class="text-sm text-slate-400">
              Objetivo: {{ generatedFor?.objetivo.replace("_", " ") }} • Nivel: {{ generatedFor?.nivel }}
            </p>
          </div>
          <div class="bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700 text-xs font-semibold text-emerald-300 w-fit">
            ⏱ {{ rutina.tiempo_total_estimado }} min estimados
          </div>
        </div>

        <p class="text-sm text-slate-400">{{ rutina.modo === 'demo' ? 'Demostración local · Rutina creada con reglas predefinidas, sin IA ni conexión externa.' : 'Rutina generada con IA · Revisa la propuesta antes de entrenar.' }}</p>
        <!-- Calentamiento -->
        <div class="bg-slate-950 p-4 rounded-xl border border-slate-800/80">
          <h3 class="text-xs uppercase tracking-wider font-semibold text-emerald-400 mb-1">
            Fase 1: Activación y Calentamiento
          </h3>
          <p class="text-sm text-slate-300">{{ rutina.calentamiento }}</p>
        </div>

        <!-- Lista de Ejercicios -->
        <div class="space-y-3">
          <h3 class="text-xs uppercase tracking-wider font-semibold text-emerald-400">
            Fase 2: Ejercicios Principales
          </h3>
          <div class="grid gap-3">
            <div
              v-for="(ejercicio, index) in rutina.ejercicios"
              :key="index"
              class="p-4 bg-slate-950 rounded-xl border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-bold text-emerald-400 bg-emerald-950/70 border border-emerald-800 px-2 py-0.5 rounded">
                    #{{ index + 1 }}
                  </span>
                  <h4 class="font-bold text-white text-base">{{ ejercicio.nombre }}</h4>
                </div>
                <p class="text-xs text-slate-400">💡 {{ ejercicio.consejo_tecnico }}</p>
              </div>

              <div class="flex items-center gap-4 text-xs font-medium text-slate-300 bg-slate-900 px-3 py-2 rounded-lg border border-slate-800">
                <div>
                  <span class="text-slate-400 block">Series</span>
                  <span class="font-bold text-white">{{ ejercicio.series }}</span>
                </div>
                <div class="h-6 w-px bg-slate-800" />
                <div>
                  <span class="text-slate-400 block">Reps</span>
                  <span class="font-bold text-white">{{ ejercicio.repeticiones }}</span>
                </div>
                <div class="h-6 w-px bg-slate-800" />
                <div>
                  <span class="text-slate-400 block">Descanso</span>
                  <span class="font-bold text-white">{{ ejercicio.descanso_segundos }}s</span>
                </div>
                <div class="h-6 w-px bg-slate-800" />
                <div>
                  <span class="text-slate-400 block">Esfuerzo</span>
                  <span class="font-bold text-emerald-400">{{ ejercicio.rpe_sugerido }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Plan de contingencia -->
        <div class="p-4 bg-emerald-950/20 border border-emerald-800/40 rounded-xl">
          <h3 class="text-xs font-bold uppercase tracking-wider text-emerald-300 mb-1">
            ¿Máquina ocupada? (Alternativa rápida)
          </h3>
          <p class="text-xs text-slate-300">{{ rutina.alternativa_rapida }}</p>
        </div>
      </article>

      <footer class="text-center text-xs text-slate-400 pb-4">FitAdaptAI · Una sesión a tu medida.<br>Propuesta orientativa. Ajusta la carga a tu capacidad y detente si aparece dolor.<br>RPE indica el esfuerzo percibido en una escala del 1 al 10.</footer>
    </div>
  </main>
</template>
