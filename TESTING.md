# Batería de calidad de FitAdaptAI

## Qué se comprueba

| Capa | Casos | Dependencias externas |
| --- | --- | --- |
| Vue / Vitest | Valores y contrato de envío, selección de material, renderizado, bloqueo durante carga, doble envío, timeout, errores de red/servidor, reintento, eliminación de resultados anteriores, texto escapado | `fetch` simulado |
| FastAPI / Pytest | Contrato HTTP, campos obligatorios, tipos y límites, configuración, construcción de la petición al proveedor, JSON y markdown, respuestas corruptas, errores 401/429/conexión/timeout, ausencia de filtración de mensajes internos | Proveedor simulado; conexiones externas bloqueadas |
| Generador demo | 31 subconjuntos de equipamiento × 4 objetivos × 3 niveles × 12 duraciones: 4.464 combinaciones, además de la regresión original | Ninguna |
| Playwright | Aplicación compilada + FastAPI real en demo, teclado, carga, reintento, desconexión, timeout y análisis automático WCAG A/AA | Solo servidores locales; fallos de IA simulados |

Se utiliza Google Chrome instalado en el equipo (`channel: chrome`), con perfiles de escritorio y emulación móvil Pixel 7. La emulación no sustituye una prueba en un teléfono físico. Los escáneres de accesibilidad no sustituyen una revisión manual con lector de pantalla.

## Instalación

Desde la raíz de FitAdaptAI, utiliza Node.js 22 LTS actualizado y Python 3.12. Con el entorno `.venv` ya creado:

```powershell
npm ci
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npx playwright install chrome ffmpeg
```

En Linux/macOS utiliza `.venv/bin/python`; en Linux instala también las dependencias del sistema con `npx playwright install --with-deps chrome ffmpeg`.

## Ejecución

```powershell
npm run test:all
```

El comando se detiene si falla alguna capa. Incluye comprobación de tipos, cobertura Vue, pruebas Python y Playwright; este último compila la aplicación antes de iniciar el navegador.

Para trabajar en una sola capa:

```powershell
npm test
npm run test:coverage
npm run test:api
npm run test:e2e -- --project=chrome
npm run test:e2e:ui
npm run test:e2e:report
```

El lanzador de Python usa `.venv` si existe; en caso contrario usa `python` del sistema. Se puede establecer `PYTHON` con la ruta de otro intérprete.

## Aislamiento y resultados

- Playwright crea sus servidores en `127.0.0.1:4179` y `127.0.0.1:8019` y los detiene al terminar. Si están ocupados, falla en vez de reutilizar un servidor de trabajo con IA real.
- El servidor E2E fuerza modo demo, deshabilita la lectura de `.env`, vacía la clave y dirige cualquier proveedor accidental a un puerto local cerrado. No se requieren secretos ni se llama a producción.
- Pytest elimina las credenciales de cada prueba, bloquea el constructor real de OpenAI y las conexiones externas. Solo permite el loopback que necesita asyncio en Windows.
- Vitest desmonta componentes y restaura simulaciones y temporizadores entre pruebas. Los fixtures representan respuestas controladas y no rutinas médicas validadas.
- Informes: `coverage/vue/index.html`, `coverage/python/index.html` y `playwright-report/index.html`. Las trazas, capturas y vídeos de fallos se conservan en `test-results/`.
- Umbrales: Vue 90 % de líneas, sentencias y funciones y 85 % de ramas; Python 90 % de cobertura combinada de líneas y ramas. Se excluyen arranque/tipos del cliente y código de pruebas del servidor. Cobertura alta no garantiza ausencia de errores.
- `.gitignore` y `.vercelignore` excluyen informes y artefactos. Las pruebas no se incluyen en el despliegue.

## Integración continua

`.github/workflows/tests.yml` ejecuta la batería en cada push y pull request y conserva informes durante 14 días, incluso si falla. Está preparado para un repositorio cuya raíz sea **FitAdaptAI**. Si se sube toda la carpeta de prácticas, hay que mover el workflow a la raíz del repositorio y ajustar `working-directory`, las rutas de caché y las de informes a `FitAdaptAI/`.

La batería no verifica el servicio de IA real, cuotas, calidad semántica de todas las rutinas ni las reglas de despliegue de Vercel. Después de publicar, sigue siendo necesaria una comprobación de `/api/health` y del flujo de generación.

Referencias: [configuración de Playwright](https://playwright.dev/docs/test-configuration), [trazas y capturas](https://playwright.dev/docs/test-use-options), [cobertura de Vitest](https://vitest.dev/guide/coverage).

## Validación realizada el 30 de septiembre de 2026

- Comprobación de tipos y compilación: correctas.
- Vue: 16 pruebas pasan; cobertura instrumentada de `App.vue`: 100 % de líneas, sentencias, funciones y ramas.
- FastAPI: 99 pruebas pasan; 100 % de líneas y 98,5 % de cobertura combinada con ramas.
- Playwright: 14 pruebas pasan con Google Chrome, 7 en escritorio y 7 con emulación móvil, incluido axe en formulario, resultado y error.
- `npm run test:all`: ejecución completa correcta con Google Chrome.
- GitHub Actions: workflow preparado; no se ha ejecutado en un repositorio remoto.

La batería permitió corregir el contraste de los textos secundarios y reconocer explícitamente `DOMException` al gestionar la cancelación de peticiones. Estos cambios se han verificado localmente; no se han desplegado de nuevo en Vercel.
