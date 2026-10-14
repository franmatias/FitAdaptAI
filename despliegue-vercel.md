# Tutorial guiado: publica FitAdaptAI en Vercel

**Objetivo:** terminar con una dirección `https://…vercel.app` donde se abra la aplicación, responda la API y se pueda generar una rutina. Puedes completar todo el recorrido en **modo demo**, sin clave de IA. Después podrás activar el **modo IA** con tu propia clave.

**Tiempo orientativo:** 30–45 minutos si ya tienes instalado Git y el proyecto funciona en tu ordenador. Las pantallas de GitHub y Vercel pueden cambiar de nombre; busca las opciones equivalentes indicadas en cada paso.

> **Importante para la clase:** cada alumno debe usar sus propias cuentas y, si activa la IA, su propia clave. No copies una clave del profesor, de otra persona ni de este tutorial. Una web pública puede recibir peticiones de cualquier visitante y consumir la cuota de la cuenta de IA.

## Mapa del despliegue (UML)

Este diagrama muestra **dónde se instala cada parte** y cómo se comunican después de publicar. Las flechas discontinuas representan la publicación del código; las flechas continuas representan las peticiones durante el uso.

```mermaid
flowchart LR
    subgraph equipo["«device» Equipo del alumno"]
        navegador["«executionEnvironment» Navegador<br/>FitAdaptAI · Vue 3"]
    end

    subgraph github["«node» GitHub"]
        repositorio["«artifact» Repositorio FitAdaptAI<br/>src/ · api/ · configuración"]
    end

    subgraph vercel["«node» Vercel · proyecto FitAdaptAI"]
      },
      "headers": [
        {
          "source": "/(.*)",
          "headers": [
            { "key": "Strict-Transport-Security", "value": "max-age=31536000" },
            { "key": "X-Content-Type-Options", "value": "nosniff" },
            { "key": "X-Frame-Options", "value": "DENY" },
            { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
            { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()" },
            { "key": "Content-Security-Policy", "value": "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; upgrade-insecure-requests" }
          ]
        }
      ]
        estaticos["«artifact» Frontend compilado<br/>Vite → dist/"]
        funcion["«executionEnvironment» Función Python<br/>api/index.py · FastAPI"]
        variables["«artifact» Variables de entorno<br/>FITADAPT_MODE · OPENAI_API_KEY · AI_MODEL"]
    **Qué hace:** Vercel construirá la interfaz como Vite y reconocerá `api/index.py` como la función Python. La aplicación FastAPI ya define `/api/health` y `/api/generate-routine`; Vercel puede entregar esas rutas a `api/index.py` sin la regla `rewrites` del ejemplo inicial. Los 60 segundos dan margen a una respuesta lenta del proveedor de IA. La aplicación tiene un tiempo de espera propio más corto; este valor no obliga a esperar siempre 60 segundos. Las cabeceras aplican HSTS, evitan MIME sniffing e iframes, limitan permisos del navegador y restringen recursos con CSP. Si en el futuro integras scripts, fuentes o servicios externos, actualiza la CSP solo para los orígenes concretos que necesites. Consulta [el ejemplo de rutas de Vercel](https://vercel.com/academy/python-on-vercel/explore-fastapi-starter) y [la configuración de duración de funciones](https://vercel.com/docs/functions/configuring-functions/duration).

    subgraph proveedor["«node» Proveedor de IA"]
        ia["«service» API de modelos"]
    end

    repositorio -. "Git: cada nuevo despliegue" .-> estaticos
    repositorio -. "Git: código Python" .-> funcion
    navegador -- "HTTPS: carga la web" --> estaticos
    navegador -- "HTTPS: POST /api/generate-routine" --> funcion
    variables -- "solo en el servidor" --> funcion
    funcion -- "HTTPS: modo ia" --> ia
    ia -- "rutina JSON" --> funcion
    funcion -- "rutina JSON" --> navegador
```

**Cómo leerlo:** GitHub almacena los archivos del proyecto. Vercel compila `src/` en una web estática y ejecuta `api/index.py` como función. El navegador solicita la rutina a la función, que usa el catálogo local en **modo demo** o consulta al proveedor en **modo IA**. La clave queda en las variables del servidor y no viaja al navegador. La flecha hacia el proveedor solo se utiliza en modo IA.

## 0. Comprueba qué vas a publicar

Abre una terminal **PowerShell dentro de la carpeta `FitAdaptAI`**, la que contiene `package.json`, `requirements.txt`, `src/` y `api/`. Si descargas el proyecto como ZIP, descomprímelo antes.

```powershell
git --version
node --version
npm --version
npm ci
npm run build
npm test
```

**Qué compruebas:** Git permite enviar el proyecto a GitHub; Node y npm construyen la interfaz; `npm run build` revisa los tipos y crea `dist/`; `npm test` ejecuta las pruebas del navegador. Si falta Git o Node, instálalos desde sus sitios oficiales y abre una terminal nueva. Si aparece un error, resuélvelo antes de publicar: Vercel ejecutará una compilación parecida.

**Resultado esperado:** el comando de compilación termina correctamente y se crea `dist/`. No subas `dist/`: Vercel la generará por ti.

## 1. Crea tu cuenta de GitHub

1. Entra en [GitHub](https://github.com/signup) y crea una cuenta personal.
2. Confirma la dirección de correo desde el mensaje que recibas. Sin verificarla, algunas acciones como crear repositorios pueden estar limitadas.
3. Activa la autenticación en dos pasos en la configuración de seguridad. Guarda sus códigos de recuperación en un lugar privado.

**Por qué:** GitHub guardará el código y Vercel leerá desde allí cada versión que quieras publicar. [Guía oficial de creación y seguridad de la cuenta de GitHub](https://docs.github.com/en/get-started/onboarding/getting-started-with-your-github-account).

## 2. Prepara el proyecto para Vercel

Abre `vercel.json` en un editor y **comprueba** que tiene este contenido (el proyecto ya lo incluye):

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "functions": {
    "api/index.py": {
      "maxDuration": 60
    }
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "Strict-Transport-Security", "value": "max-age=31536000" },
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()" },
        { "key": "Content-Security-Policy", "value": "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; upgrade-insecure-requests" }
      ]
    }
  ]
}
```

**Qué hace:** Vercel construirá la interfaz como Vite y reconocerá `api/index.py` como la función Python. La aplicación FastAPI ya define `/api/health` y `/api/generate-routine`; Vercel puede entregar esas rutas a `api/index.py` sin la regla `rewrites` del ejemplo inicial. Los 60 segundos dan margen a una respuesta lenta del proveedor de IA. La aplicación tiene un tiempo de espera propio más corto; este valor no obliga a esperar siempre 60 segundos. Las cabeceras activan HSTS, evitan MIME sniffing e iframes y limitan los recursos que puede cargar el navegador con CSP. Si en el futuro añades scripts, estilos o servicios externos, permite solo los orígenes que realmente necesites. Consulta [el ejemplo de rutas de Vercel](https://vercel.com/academy/python-on-vercel/explore-fastapi-starter) y [la configuración de duración de funciones](https://vercel.com/docs/functions/configuring-functions/duration).

**Comprueba:** `vercel.json` es JSON válido, sin comentarios ni comas sobrantes. Conserva `api/index.py`, `api/demo.py`, `package.json`, `package-lock.json` y `requirements.txt` dentro de `FitAdaptAI`. Vercel instala dependencias Python desde `requirements.txt` y actualmente admite Python 3.12 como versión predeterminada cuando no se fija otra versión compatible. [Documentación del runtime Python](https://vercel.com/docs/functions/runtimes/python).

## 3. Revisa los secretos antes de subir nada

El archivo local `.env` puede contener una clave real. **No lo abras para copiar su contenido a GitHub.** En este proyecto `.gitignore` excluye `.env`, `node_modules/`, `.venv/` y `dist/`. `.env.example` es solo una plantilla sin claves.

Desde la carpeta `FitAdaptAI`, ejecuta:

```powershell
git init
git check-ignore .env
git status --short
```

Si tienes un `.env`, el segundo comando debe mostrar `.env`. Si **no** lo muestra, comprueba que estás en `FitAdaptAI`, que `.gitignore` contiene una línea `.env` y detente antes de `git add`. En `git status --short` no debe figurar `.env` ni una clave. Si ya habías subido una clave a cualquier repositorio, quitar el archivo en un commit nuevo no borra el historial: revoca esa clave y crea otra.

**Nunca** escribas la clave en `src/`, `public/`, `vite.config.ts`, `vercel.json`, una captura de pantalla, un commit, un issue o el tutorial. Las variables con prefijo `VITE_` quedan disponibles para el código del navegador: no utilices ese prefijo para `OPENAI_API_KEY`. La clave se usa exclusivamente en FastAPI.

## 4. Crea un repositorio en GitHub y sube el proyecto

1. En GitHub, pulsa **New repository** (o entra en [Crear repositorio](https://github.com/new)).
2. Elige tu cuenta como propietario y usa un nombre como `fitadaptai-alumno`.
3. Para esta práctica, selecciona **Private**. Podrás enseñar la URL de la aplicación sin publicar el código. Si tu profesor exige un repositorio público, revísalo antes de cambiar su visibilidad.
4. Deja sin marcar la creación de README, `.gitignore` y licencia, porque el proyecto ya tiene esos archivos.
5. Pulsa **Create repository** y copia la URL HTTPS que te ofrece GitHub.

En la terminal de `FitAdaptAI`:

```powershell
git add .
git status --short
git commit -m "Preparar FitAdaptAI para Vercel"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/fitadaptai-alumno.git
git push -u origin main
```

Sustituye `TU_USUARIO` y el nombre del repositorio por los tuyos. Si Git pide nombre y correo para el primer commit, configúralos siguiendo el mensaje que aparece. Para iniciar sesión al hacer `push`, sigue el flujo de autenticación de GitHub; **no pegues la clave de OpenAI como contraseña de GitHub**.

**Punto de control:** abre el repositorio en el navegador. Debes ver `api/`, `src/`, `package.json` y `despliegue-vercel.md`. **No** debes ver `.env`, `.venv/` ni `node_modules/`. [Crear un repositorio en GitHub](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository).

> Si ya habías inicializado Git en la carpeta superior `practica01`, no inicialices otro repositorio encima sin decidir primero cómo organizarlo. Puedes usar el repositorio superior y, al importar en Vercel, establecer **Root Directory = `FitAdaptAI`**. Si el repositorio es solo esta carpeta, deja **Root Directory = `.`**.

## 5. Crea tu cuenta de Vercel

1. Entra en [Vercel](https://vercel.com/signup).
2. Para este recorrido, regístrate con la misma cuenta de **GitHub**. Así podrás seleccionar el repositorio directamente. Si eliges registrarte por correo, después tendrás que conectar GitHub.
3. Si Vercel te pide autorizar el acceso a GitHub, concede acceso solo al repositorio de la práctica cuando esa opción esté disponible. Puedes revisar o revocar la integración más tarde desde GitHub.
4. Selecciona el espacio personal. **Hobby** sirve para aprender y para proyectos personales, sujeto a sus límites de uso. Revisa el plan que aparece antes de aceptar cambios de plan o facturación.

[Información oficial de cuentas de Vercel](https://vercel.com/docs/accounts) y [plan Hobby](https://vercel.com/docs/plans/hobby).

## 6. Importa FitAdaptAI en Vercel

1. En el panel de Vercel, pulsa **Add New → Project** o **New Project**.
2. Busca tu repositorio `fitadaptai-alumno` y pulsa **Import**. Si no aparece, revisa la conexión con GitHub y los permisos concedidos al repositorio.
3. En **Project Name**, puedes usar `fitadaptai-alumno`. El nombre debe estar disponible; Vercel te avisará si no lo está.
4. En **Framework Preset**, elige **Vite** si no aparece detectado.
5. En **Root Directory**, elige `.` si `package.json` está en la raíz del repositorio. Si subiste la carpeta `practica01` entera, elige `FitAdaptAI`.
6. Comprueba **Build Command = `npm run build`** y **Output Directory = `dist`**. Si Vercel los detectó correctamente, no hace falta sobrescribirlos. Mantén la instalación automática de dependencias basada en `package-lock.json`.

**Por qué:** Vercel debe encontrar en la misma raíz de proyecto el frontend Vite y la carpeta `api/`. Una raíz incorrecta suele producir errores de `package.json` ausente o una web sin API. [Importar repositorios](https://vercel.com/docs/git) y [configuración de la compilación y la raíz](https://vercel.com/docs/builds/configure-a-build).

## 7. Elige el modo antes del primer despliegue

### Ruta recomendada para empezar: demo

En **Environment Variables**, añade:

| Nombre | Valor | Entorno |
| --- | --- | --- |
| `FITADAPT_MODE` | `demo` | Production |

No añadas `OPENAI_API_KEY`. El modo demo genera rutinas con reglas locales y permite comprobar todo el recorrido sin consumir una API externa. Si quieres probar una rama de GitHub en una URL de prueba, añade también `FITADAPT_MODE=demo` al entorno **Preview**.

### Ruta opcional: IA real

**Límite de seguridad:** el endpoint de generación no tiene autenticación ni limitación de solicitudes persistente; cualquier visitante puede llamarlo y generar consumo de la clave. No publiques el modo IA en un dominio público hasta configurar reglas de rate limiting para `/api/generate-routine` en Vercel Firewall/WAF (si están incluidas en tu plan) o poner autenticación y un límite equivalente delante de la API. Configura además alertas y límites de gasto en el proveedor de IA. Si no puedes aplicar esos controles, mantén `FITADAPT_MODE=demo`.

Usa **una clave propia** de un proyecto de OpenAI al que tengas acceso y revisa sus límites de uso antes de publicar. En Vercel, añade estas variables al entorno **Production**:

| Nombre | Valor |
| --- | --- |
| `FITADAPT_MODE` | `ia` |
| `OPENAI_API_KEY` | tu clave privada, introducida en el formulario de Vercel |
| `AI_MODEL` | `gpt-4o-mini` o un modelo disponible en tu proyecto |

No copies la clave a este fichero ni a GitHub. Si Vercel ofrece marcar la variable como **Sensitive**, úsalo para `OPENAI_API_KEY`. Si también quieres probar IA en **Preview**, configura allí variables separadas; una rama de prueba no recibe automáticamente las variables de Production. El valor `AI_MODEL` del ejemplo debe corresponder a un modelo al que tu proyecto tenga acceso. OpenAI puede cobrar por las llamadas, independientemente del plan de Vercel.

**Consejo docente:** para una práctica en clase, empieza con `demo`. Una web pública en modo `ia` expone el botón de generación a cualquier visitante y puede generar consumo de la cuenta. Usa una clave de proyecto específica para esta práctica, controla el uso y desactiva `ia` al terminar si ya no lo necesitas.

Las variables de entorno se aplican a **nuevos despliegues**. Si las cambias después, vuelve a desplegar desde la pestaña **Deployments**; recargar la página publicada no basta. [Entornos y variables de Vercel](https://vercel.com/docs/environment-variables).

## 8. Publica y comprueba

1. Pulsa **Deploy**. Espera a que Vercel muestre el despliegue como listo. Si aparece un error, abre **Build Logs** y consulta la tabla de ayuda del paso 10.
2. Abre la URL pública que Vercel te muestra. Debe cargar el formulario de FitAdaptAI con sus cuatro controles.
3. Añade `/api/health` al final del dominio, por ejemplo `https://tu-proyecto.vercel.app/api/health`. Debes recibir un JSON con `"status":"ok"` y `"modo":"demo"` o `"modo":"ia"`.
4. Comprueba las cabeceras de seguridad con `curl.exe -I https://tu-proyecto.vercel.app/`: busca `content-security-policy`, `strict-transport-security`, `x-content-type-options` y `x-frame-options`.
5. Vuelve a la página principal, elige objetivo, duración, nivel y equipamiento, y pulsa **Generar mi rutina**. Comprueba que aparecen calentamiento, ejercicios, descanso, consejo técnico y alternativa.
6. Si elegiste demo, la página debe identificar la rutina como demostración local. Si elegiste IA, debe mostrarla como rutina generada con IA.

**Evidencia para entregar al profesor:** URL del despliegue, captura de la pantalla principal y captura de una rutina generada. No incluyas variables de entorno ni claves en las capturas. La URL `/api/health` verifica el servidor; ver solo la pantalla principal no demuestra que la API funcione.

## 9. Actualiza tu proyecto

Cada vez que cambies código o este tutorial, comprueba el proyecto en local y publica una nueva versión:

```powershell
npm run build
npm test
git status --short
git add .
git commit -m "Explicar el cambio realizado"
git push
```

Si la rama enviada es `main`, Vercel iniciará normalmente un nuevo despliegue de **Production**. Las otras ramas generan despliegues **Preview**. Espera a que termine y vuelve a probar `/api/health` y una rutina. [Despliegues desde Git](https://vercel.com/docs/git).

## 10. Si algo falla

| Síntoma | Qué revisar y cómo seguir |
| --- | --- |
| GitHub o Vercel no muestran el repositorio | Confirma el correo de GitHub, la cuenta conectada y que la integración de Vercel tiene permiso para este repositorio. |
| `package.json` no encontrado, compilación fallida o `dist` ausente | Corrige **Root Directory** para que apunte a la carpeta que contiene `package.json`. Comprueba que `npm run build` termina en local. |
| La página abre, pero `/api/health` devuelve 404 | Confirma que `api/index.py` y `api/demo.py` están en el repositorio y que `vercel.json` coincide con el paso 2. Despliega de nuevo. |
| `/api/health` devuelve 500 | Revisa **Runtime Logs** de la función y que `requirements.txt` está en la raíz seleccionada. No copies registros que contengan datos sensibles a un repositorio público. |
| El modo mostrado no es el esperado | Comprueba `FITADAPT_MODE` en el entorno del despliegue que estás abriendo: **Production** o **Preview**. Vuelve a desplegar tras cambiarlo. |
| La rutina falla con un mensaje de clave ausente | En modo IA, configura `OPENAI_API_KEY` en el servidor para ese entorno; en modo demo, usa `FITADAPT_MODE=demo`. Despliega de nuevo. |
| Error del proveedor o demora | Comprueba acceso al modelo indicado por `AI_MODEL`, estado de la cuenta de IA y límites de uso. Haz una prueba con pocos alumnos a la vez. Revisa los registros de la función sin publicar la clave. |
| Función interrumpida por tiempo | Comprueba el `maxDuration` del paso 2 y los límites del plan. La petición al proveedor puede tardar; evita aumentar tiempos sin revisar el consumo. |

**Última comprobación:** abre la dirección pública en una ventana privada del navegador. Así sabrás si la práctica funciona para alguien que no ha iniciado sesión en tu equipo. Si Vercel ha activado protección de acceso para el despliegue, comparte con el profesor la forma de acceso prevista por la plataforma, sin enviar contraseñas ni claves de API en capturas.

## Fuentes para consultar si la interfaz cambia

- [Vercel: desplegar desde Git](https://vercel.com/docs/git)
- [Vercel: FastAPI y rutas de `api/index.py`](https://vercel.com/academy/python-on-vercel/explore-fastapi-starter)
- [Vercel: variables de entorno](https://vercel.com/docs/environment-variables)
- [Vercel: configurar builds](https://vercel.com/docs/builds/configure-a-build)
- [GitHub: empezar con una cuenta](https://docs.github.com/en/get-started/onboarding/getting-started-with-your-github-account)
