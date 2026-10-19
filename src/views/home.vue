<script setup lang="ts">
import { computed } from 'vue';
import { UserButton, useAuth } from '@clerk/vue';
import { RouterLink } from 'vue-router';
import App from '../App.vue';

const e2eAuth = import.meta.env.VITE_E2E_AUTH === 'true';
const auth = e2eAuth ? undefined : useAuth();
const isLoaded = computed(() => e2eAuth || Boolean(auth?.isLoaded.value));
const isSignedIn = computed(() => e2eAuth || Boolean(auth?.isSignedIn.value));
const getSessionToken = (): Promise<string | null> =>
  e2eAuth ? Promise.resolve('e2e-session-token') : auth?.getToken.value() ?? Promise.resolve(null);
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100">
    <header class="mx-auto flex max-w-4xl justify-end px-4 pt-4 sm:px-6 lg:px-8">
      <UserButton v-if="isSignedIn && !e2eAuth" />
    </header>

    <div v-if="!isLoaded" class="py-16 text-center text-slate-300" role="status">
      Cargando sesión…
    </div>
    <template v-else-if="isSignedIn">
      <App :get-token="getSessionToken" />
    </template>
    <template v-else>
      <main class="mx-auto max-w-xl px-4 py-16 text-center">
        <h1 class="text-3xl font-bold text-white">Bienvenido a FitAdapt AI</h1>
        <p class="mt-4 text-slate-300">Inicia sesión o crea una cuenta para diseñar tu rutina.</p>
        <nav class="mt-8 flex justify-center gap-4">
          <RouterLink
            to="/sign-in"
            class="rounded-xl bg-emerald-500 px-5 py-3 font-semibold text-slate-950 hover:bg-emerald-400"
          >
            Iniciar sesión
          </RouterLink>
          <RouterLink
            to="/sign-up"
            class="rounded-xl border border-slate-600 px-5 py-3 font-semibold text-white hover:bg-slate-800"
          >
            Crear cuenta
          </RouterLink>
        </nav>
      </main>
    </template>
  </div>
</template>
