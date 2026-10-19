import { clerkPlugin } from '@clerk/vue';
import { createApp } from 'vue';
import AppRoot from './AppRoot.vue';
import { router } from './router';
import './style.css';

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
const E2E_AUTH = import.meta.env.VITE_E2E_AUTH === 'true';
if (!PUBLISHABLE_KEY && !E2E_AUTH) {
  throw new Error('Falta VITE_CLERK_PUBLISHABLE_KEY. Configúrala en .env con las claves de tu aplicación Clerk.');
}

const app = createApp(AppRoot);
if (PUBLISHABLE_KEY && !E2E_AUTH) {
  app.use(clerkPlugin, {
    publishableKey: PUBLISHABLE_KEY,
    signInUrl: '/sign-in',
    signUpUrl: '/sign-up',
    signInFallbackRedirectUrl: '/',
    signUpFallbackRedirectUrl: '/',
  });
}
app.use(router);
app.mount('#root');
