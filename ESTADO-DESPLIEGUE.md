# Estado de preparación del despliegue

Fecha: 15 de octubre de 2026. Este registro distingue las comprobaciones realizadas de las instrucciones todavía pendientes de ejecutar.

## Realizado y verificado

- Seleccionada `FitAdaptAI` como carpeta principal; la copia vecina `fitadaptai-deploy` no se ha modificado.
- Creada la guía `DESPLIEGUE-GITHUB-AWS.md` con publicación segura, instalación de herramientas, Docker, Academy/EC2, cuenta de pago/ECR/ECS, HTTPS, secretos, mantenimiento y eliminación de recursos.
- Ampliado `.gitignore` para claves privadas, credenciales AWS, SSH y archivos locales de despliegue.
- Verificadas las reglas primero en un repositorio temporal y después en el repositorio local: `.env`, `.env.local`, `.env.docker`, credenciales AWS/SSH y claves privadas se ignoran; `.env.example` se permite.
- Inicializado el repositorio Git local con rama `main`. Preparados 51 archivos; entre los nombres reservados para entornos y claves solo está versionada la plantilla `.env.example`. La búsqueda inicial de patrones de claves AWS, proveedor IA y claves privadas no encontró coincidencias.
- Añadidos Dockerfile multietapa, `.dockerignore`, Compose y entrada Python que sirve cliente y API en el mismo origen.
- Docker Desktop arrancado; motor Linux disponible. Versiones comprobadas: Docker Engine 29.8.1 y Docker Desktop 4.93.0.
- AWS CLI v2 instalada para el usuario mediante el instalador oficial con firma válida de Amazon Web Services. Verificada versión `aws-cli/2.38.1`. Puede ser necesario abrir una terminal nueva para actualizar PATH.
- Imagen `fitadaptai:local` construida para `linux/amd64`, con Node 22 y Python 3.12. Construcción del cliente completada dentro de Docker.
- Contenedor `fitadaptai-app-1` arrancado en modo demo y estado Docker `healthy`, publicado exclusivamente en `127.0.0.1:8080`.
- Comprobadas página principal, archivos JS/CSS, cabeceras de seguridad y respuesta de `/api/health`.
- Comprobada generación de rutina demo válida y duración dentro del límite solicitado.
- Comprobados 404 para `/.env`, `/.env.local`, `/.git/config` y una ruta API inexistente.
- Comprobado que `/app` en la imagen no contiene archivos `.env*`, que el proceso utiliza UID 10001 y que no hay clave IA configurada en el contenedor de prueba.
- Pruebas de API: **99 superadas**, cobertura **98,50 %**, sin llamadas al proveedor IA.
- Compilación local del cliente completada y **16 pruebas de interfaz superadas** en tres archivos.

## Incidencias detectadas

- Algunos accesos del entorno restringido a las cachés y al sistema de archivos fallaron por permisos. La compilación Docker se completó mediante `scripts/build_container.py`, que envía un contexto temporal de archivos seleccionados. La ejecución de pruebas fuera de la restricción sí terminó correctamente.
- Al instalar las dependencias en la fase de construcción, npm informó de ocho alertas: dos moderadas y seis altas. Una consulta separada con `npm audit --omit=dev` identificó una alerta alta de `source-map-js`, asociada a [GHSA-68fv-2mgg-jv7q](https://github.com/advisories/GHSA-68fv-2mgg-jv7q). La imagen final sirve archivos estáticos y no contiene Node ni `node_modules`; aun así, revisar y corregir las dependencias afectadas, reconstruir y repetir las pruebas antes de publicar. No se han aplicado actualizaciones automáticas que puedan cambiar el comportamiento.
- Las pruebas emitieron una advertencia de `cache_dir` porque se deshabilitó el plugin de caché para evitar los permisos locales; las 99 pruebas y el umbral de cobertura pasaron.

## Pendiente para completar los objetivos externos

1. Cuenta GitHub confirmada: `franmatias`; nombre propuesto del repositorio: `fitadaptai`, privado. El navegador integrado no tenía sesión iniciada y se ha dejado abierto el formulario de acceso. Falta crear o identificar el repositorio remoto y publicar el primer commit; no se ha publicado ningún archivo.
2. Revisar las alertas de dependencias y validar las correcciones antes del despliegue público.
3. Abrir una sesión autorizada del Learner Lab, comprobar restricciones, elegir región y desplegar EC2. No se ha creado ningún recurso Academy.
4. La cuenta AWS de pago queda aplazada por indicación del responsable. En esa fase se preparará un perfil autorizado, se confirmarán región y presupuesto y se crearán ECR/ECS/ALB. No se han creado recursos de pago ni configurado credenciales AWS.
5. Identificar un dominio controlado para HTTPS.
6. Si se desea modo IA accesible por Internet, completar control de acceso y límites de uso, configurar el secreto y realizar una prueba de consumo autorizada. Esta sesión solo ha utilizado demo.

## Uso local

La versión Docker queda disponible en http://127.0.0.1:8080 mientras Docker Desktop esté activo. Para detenerla, ejecutar `docker compose down` desde la carpeta FitAdaptAI. No se ha modificado el despliegue de Vercel.
