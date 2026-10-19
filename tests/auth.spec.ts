import { flushPromises, mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import { router } from '../src/router';
import HomeView from '../src/views/home.vue';
import SignInView from '../src/views/sign-in.vue';
import SignUpView from '../src/views/sign-up.vue';

const clerkState = vi.hoisted(() => ({
  isLoaded: true,
  isSignedIn: false,
  getToken: vi.fn().mockResolvedValue('session-token'),
}));

vi.mock('@clerk/vue', async () => {
  const { ref } = await import('vue');
  return {
    SignIn: { template: '<div data-testid="clerk-sign-in">Sign in</div>' },
    SignUp: { template: '<div data-testid="clerk-sign-up">Sign up</div>' },
    UserButton: { template: '<button data-testid="clerk-user-button">Account</button>' },
    useAuth: () => ({
      isLoaded: ref(clerkState.isLoaded),
      isSignedIn: ref(clerkState.isSignedIn),
      getToken: ref(clerkState.getToken),
    }),
  };
});

const global = {
  stubs: {
    RouterLink: { template: '<a><slot /></a>' },
  },
};

describe('Clerk authentication views', () => {
  it('shows sign-in and sign-up controls to signed-out visitors', () => {
    clerkState.isLoaded = true;
    clerkState.isSignedIn = false;

    const wrapper = mount(HomeView, { global });

    expect(wrapper.text()).toContain('Inicia sesión o crea una cuenta');
    expect(wrapper.text()).toContain('Iniciar sesión');
    expect(wrapper.text()).toContain('Crear cuenta');
    expect(wrapper.find('form').exists()).toBe(false);
  });

  it('shows the workout app and forwards a Clerk session token when signed in', async () => {
    clerkState.isLoaded = true;
    clerkState.isSignedIn = true;
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        calentamiento: 'Movilidad suave',
        ejercicios: [{
          nombre: 'Sentadilla',
          series: 3,
          repeticiones: '8-10',
          descanso_segundos: 60,
          rpe_sugerido: 'RPE 6',
          consejo_tecnico: 'Mantén la espalda recta.',
        }],
        alternativa_rapida: 'Zancadas',
        tiempo_total_estimado: 30,
      }),
    });
    vi.stubGlobal('fetch', mockFetch);

    const wrapper = mount(HomeView, { global });
    expect(wrapper.find('[data-testid="clerk-user-button"]').exists()).toBe(true);
    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/generate-routine',
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer session-token' }),
      }),
    );
  });

  it('waits for Clerk to finish loading the current session', () => {
    clerkState.isLoaded = false;
    clerkState.isSignedIn = false;

    const wrapper = mount(HomeView, { global });

    expect(wrapper.get('[role="status"]').text()).toContain('Cargando sesión');
    expect(wrapper.find('form').exists()).toBe(false);
  });

  it('registers the root, sign-in, and sign-up routes', () => {
    expect(router.getRoutes().map(({ path }) => path).sort()).toEqual([
      '/',
      '/sign-in',
      '/sign-up',
    ]);
  });

  it('renders Clerk sign-in and sign-up components on their routes', () => {
    expect(mount(SignInView).find('[data-testid="clerk-sign-in"]').exists()).toBe(true);
    expect(mount(SignUpView).find('[data-testid="clerk-sign-up"]').exists()).toBe(true);
  });
});
