# Presentación directa de pruebas de seguridad

Cada caso muestra en una diapositiva:

1. Vulnerabilidad.
2. Cómo se defendió.
3. Comando exacto a ejecutar.
4. Qué hará la prueba.
5. Captura del resultado real.

## Archivos

- `Pruebas_Seguridad.pptx`: editable, con portada y 20 casos.
- `Pruebas_Seguridad.pdf`: la misma presentación lista para proyectar.
- `COMANDOS_Y_PASOS.md`: comandos para copiar, resultados y alternativas manuales.
- `capturas/`: 20 capturas PNG de la salida real de las pruebas.

## Cómo usarla

Abre Docker Desktop. Desde una terminal dentro del proyecto, por ejemplo:

```bash
.venv/bin/python scripts/demo_case.py sql
```

Ejecuta únicamente el caso de la diapositiva. El resultado se imprime y se guarda en `evidence/presentacion/`.

Si también quieres mostrar la interfaz web, abre otra terminal y ejecuta `bash scripts/run.sh`; luego abre https://localhost:8443.

Todas las pruebas usan `test_consultas_presentacion`, una base separada con datos sintéticos que se crea y elimina al ejecutar el caso. La prueba `backup` restaura además en una base NUEVA; no sobrescribe la base del aplicativo. No ejecutes dos casos simultáneamente porque utilizan el mismo nombre de base de pruebas.

Las imágenes son capturas de la **salida real del comando de prueba automatizada**, no imágenes de la ventana del aplicativo. Los códigos HTTP proceden del cliente de pruebas de Django y los estados se verifican en PostgreSQL en Docker. La prueba de recuperación ejecuta `pg_dump` y `pg_restore` reales. La cuota DoS comprueba 301 solicitudes aisladas; la alternativa `scripts/load.py` mide carga HTTP sobre el aplicativo.

SQL, XSS, permisos, MFA y fuerza bruta también tienen una alternativa manual indicada en las notas y en el archivo de comandos.

No se incluyen contraseñas, claves ni códigos MFA reales en las diapositivas o capturas.

## Regenerar

```bash
.venv/bin/python scripts/demo_case.py all
.venv/bin/python scripts/capture_slide_receipts.py
.local/slides-venv/bin/python scripts/build_presentation.py
libreoffice --headless --convert-to pdf --outdir presentacion presentacion/Pruebas_Seguridad.pptx
```
