import { createRouter, createWebHistory } from 'vue-router';
import HomeView from './views/home.vue';
import SignInView from './views/sign-in.vue';
import SignUpView from './views/sign-up.vue';

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView },
    { path: '/sign-in', component: SignInView },
    { path: '/sign-up', component: SignUpView },
  ],
});
