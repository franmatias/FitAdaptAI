# FitAdaptAI

## Proyecto educativo

FitAdaptAI es un ejercicio didáctico para comprender el proceso completo de desarrollo y despliegue de una aplicación web. Consiste en una app sencilla, con frontend y backend, que utiliza una API de inteligencia artificial para resolver un problema concreto: proponer rutinas de entrenamiento adaptadas a las preferencias y restricciones de cada usuario.

El ejercicio pone especial énfasis en redactar una buena especificación y recorrer el ciclo de vida del proyecto: mantener un histórico de cambios con Git y GitHub, desplegar la aplicación en Vercel y AWS, y preparar su ejecución con Docker. También sirve para practicar la incorporación progresiva de servicios externos, como Clerk para la autenticación, y la protección de sus credenciales y demás variables de entorno. Clerk se plantea como parte de ese aprendizaje y no está integrado actualmente en la aplicación.

La aplicación está construida con Vue 3, TypeScript y Tailwind en el frontend, y FastAPI en el backend. El documento original de referencia se conserva fuera del proyecto.

## Abrir en Windows

Las dependencias se instalan en esta carpeta. Haz doble clic en **Iniciar FitAdaptAI.cmd** y abre **http://127.0.0.1:5173**. Mantén la ventana abierta mientras utilizas la aplicación; Ctrl+C detiene la sesión.

En una instalación nueva necesitas Node.js 20.18 o superior y Python 3.12 (versión comprobada). Desde esta carpeta:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

## Modos de generación

El modo **demo** funciona sin cuenta, sin clave y sin llamadas externas. Usa un catálogo de ejercicios y reglas según objetivo, nivel, equipamiento y tiempo. La duración es una estimación calculada con calentamiento, series, descansos y transiciones; puede ser inferior al tiempo disponible. La pantalla identifica cada resultado demo.

Para usar un proveedor de IA, copia `.env.example` a `.env`, cambia `FITADAPT_MODE=ia` e introduce tu clave en `OPENAI_API_KEY`. Reinicia el servidor. `.env` está excluido de Git; solo se debe compartir `.env.example`, sin claves ni valores secretos. Si una clave se publica por error, revócala y genera otra. La clave permanece en Python y nunca se incluye en el cliente. El uso del proveedor puede tener coste. `OPENAI_BASE_URL` permite configurar un endpoint compatible y `AI_MODEL` su modelo.

Si el proveedor falla se muestra un error; no se sustituye silenciosamente la respuesta por una demo. La integración real necesita una clave válida y no se comprueba mediante llamadas de pago durante las pruebas.

## Inicio manual (Windows)

En una terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.index:app --reload --host 127.0.0.1 --port 8000
```

En otra:

```powershell
npm run dev
```

En Linux/macOS: `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, `npm ci`; inicia el servidor con `.venv/bin/python -m uvicorn api.index:app --reload --host 127.0.0.1 --port 8000` y el cliente con `npm run dev` en otra terminal.

## Comprobaciones

La batería completa de Vue, FastAPI y Playwright, su instalación y sus informes están descritos en [TESTING.md](TESTING.md). Una vez instaladas las dependencias de desarrollo y los navegadores, ejecuta `npm run test:all`.

```powershell
npm run build
npm test
.\.venv\Scripts\python.exe -m pytest -q
```

La documentación interactiva de la API está en http://127.0.0.1:8000/docs. Vite redirige `/api` al servidor local. `npm run preview` solo muestra la compilación estática; para el flujo completo utiliza el inicio local anterior.

## Cambios respecto al ejemplo

- Corregido `str` a `string` en TypeScript y actualizada la herramienta de comprobación de tipos.
- Duración entera de 20 a 75 minutos en pasos de 5, equipamiento no vacío, sin duplicados, y rechazo de campos desconocidos.
- Respuestas del proveedor validadas; errores sin revelar datos internos y tiempos de espera acotados.
- Carga de `.env`, sin CORS abierto: el navegador utiliza el proxy del mismo origen.
- Formulario bloqueado durante la petición; mensajes accesibles y parámetros del resultado conservados aunque se cambien los controles.
- Modo demo explícito, arranque Windows y pruebas sin consumo de API.

Según la confirmación del responsable del proyecto, la aplicación ya está desplegada en Vercel. `vercel.json` utiliza el preset Vite y la función Python; la guía de ese entorno está en `despliegue-vercel.md`. En local, los puertos solo escuchan en la propia máquina.

## GitHub, Docker y AWS

Consulta [DESPLIEGUE-GITHUB-AWS.md](DESPLIEGUE-GITHUB-AWS.md) para publicar el código sin secretos, construir Docker y desplegar en AWS Academy y en una cuenta de pago. Los resultados verificados y los pasos pendientes están en [ESTADO-DESPLIEGUE.md](ESTADO-DESPLIEGUE.md).

Arranque Docker en modo demo, usando la construcción con selección explícita de archivos:

```powershell
.\.venv\Scripts\python.exe scripts/build_container.py
docker compose up -d --no-build
```

Abre http://127.0.0.1:8080. Para detenerlo: `docker compose down`.
