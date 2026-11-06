# Pruebas de seguridad: comandos directos

Abre Docker Desktop. Desde la carpeta del proyecto ejecuta el comando del caso. Cada prueba usa datos sintéticos y otra base; no borra tus citas. La recuperación crea además una base restore_ nueva. Las capturas son imágenes de la salida real del comando, no de la interfaz del aplicativo.

```bash
.venv/bin/python scripts/demo_case.py all
```
Este comando repite los 20 casos. Para exponer, utiliza uno a la vez.


## 01. Acceso a una cita ajena (BOLA)

**Vulnerabilidad:** Cambiar el identificador de una cita para consultar datos de otro paciente.

**Defensa:** El servidor verifica propietario, rol y ámbito en cada recurso.

```bash
.venv/bin/python scripts/demo_case.py bola
```

**Qué hará:** Crea una cita de A y comprueba que B recibe 403, mientras A puede verla.

**Qué observar:** Paciente ajeno: HTTP 403. Propietario: HTTP 200.

**Captura:** [ver imagen](capturas/01_bola.png).

**Alternativa manual:** Copiar la URL específica de A, entrar como paciente.b y pegarla.

## 02. Inyección SQL en el login

**Vulnerabilidad:** Introducir instrucciones SQL en un dato del formulario.

**Defensa:** Filtro de patrones, ORM parametrizado y usuario SQL sin permisos DDL.

```bash
.venv/bin/python scripts/demo_case.py sql
```

**Qué hará:** Envía la carga al login y prueba otra entrada que pasa el filtro sin alterar la consulta.

**Qué observar:** Payload bloqueado: 400. Entrada tratada como dato: sin resultados ajenos.

**Captura:** [ver imagen](capturas/02_sql.png).

**Alternativa manual:** Usuario: ' OR 1=1-- · Contraseña ficticia · Continuar.

## 03. Inyección de JavaScript (XSS)

**Vulnerabilidad:** Introducir JavaScript para que se ejecute en el navegador.

**Defensa:** Filtro de entrada, escape de HTML y política CSP de scripts.

```bash
.venv/bin/python scripts/demo_case.py xss
```

**Qué hará:** Envía un script al login y verifica el escape de contenido almacenado.

**Qué observar:** Login: HTTP 400. Contenido almacenado escapado y CSP presente.

**Captura:** [ver imagen](capturas/03_xss.png).

**Alternativa manual:** Usuario: <script>alert('XSS')</script> · Continuar.

## 04. Fuerza bruta de contraseñas

**Vulnerabilidad:** Probar contraseñas repetidamente hasta obtener acceso.

**Defensa:** Cuotas por cuenta e IP, error genérico, MFA y auditoría.

```bash
.venv/bin/python scripts/demo_case.py fuerza
```

**Qué hará:** Hace seis intentos erróneos con un usuario ficticio en una base separada.

**Qué observar:** El sexto intento recibe HTTP 429 y el bloqueo queda auditado.

**Captura:** [ver imagen](capturas/04_fuerza.png).

**Alternativa manual:** Login: usuario.inexistente.demo · Contraseña errónea · Seis envíos.

## 05. Saturación de solicitudes (DoS)

**Vulnerabilidad:** Enviar demasiadas solicitudes para agotar recursos de la API.

**Defensa:** Límite de 300 solicitudes por IP y minuto; respuesta 429.

```bash
.venv/bin/python scripts/demo_case.py dos
```

**Qué hará:** Hace 301 solicitudes aisladas: comprueba 300 respuestas 200 y una 429.

**Qué observar:** La solicitud 301 recibe 429 y Retry-After: 60.

**Captura:** [ver imagen](capturas/05_dos.png).

**Alternativa manual:** .venv/bin/python scripts/load.py --users 30 --seconds 10

**Alcance:** Prueba de cuota con cliente Django; no mide resistencia a un DDoS de red.

## 06. Reutilizar un código MFA anterior

**Vulnerabilidad:** Intentar usar un código consumido o de otro inicio de sesión.

**Defensa:** Desafío por sesión previa, un uso, caducidad y nuevo código en cada login.

```bash
.venv/bin/python scripts/demo_case.py mfa
```

**Qué hará:** Entra, sale, crea otro acceso y compara el rechazo del código viejo con el nuevo.

**Qué observar:** El código anterior no abre el panel; el código nuevo sí.

**Captura:** [ver imagen](capturas/06_mfa.png).

**Alternativa manual:** .venv/bin/python manage.py demo_code paciente.a

**Alcance:** La entrega por consola simula el canal del OTP de las cuentas sintéticas.

## 07. Confirmación de pago falsificada

**Vulnerabilidad:** Marcar una orden como pagada con un webhook de firma falsa.

**Defensa:** Validación HMAC del emisor antes de procesar el pago.

```bash
.venv/bin/python scripts/demo_case.py webhook
```

**Qué hará:** Crea una orden pendiente y envía su confirmación con una firma inválida.

**Qué observar:** HTTP 400. El pago permanece pendiente.

**Captura:** [ver imagen](capturas/07_webhook.png).

**Alternativa manual:** POST /integrations/psp/ · X-Scope: payments:write · Sin firma válida.

## 08. Manipular monto o moneda

**Vulnerabilidad:** Cambiar el monto o la moneda de una orden para pagar menos.

**Defensa:** Comparación contra la orden real, aunque el mensaje tenga firma válida.

```bash
.venv/bin/python scripts/demo_case.py monto
```

**Qué hará:** Envía un evento firmado con un centavo y moneda EUR sobre una orden USD.

**Qué observar:** HTTP 400. La cita no pasa a confirmada.

**Captura:** [ver imagen](capturas/08_monto.png).

## 09. Repetir un mensaje de integración

**Vulnerabilidad:** Reenviar un mensaje firmado o utilizar uno vencido.

**Defensa:** Nonce único por socio, timestamp y scope permitido.

```bash
.venv/bin/python scripts/demo_case.py replay
```

**Qué hará:** Repite un mensaje válido y ensaya una fecha antigua y un scope prohibido.

**Qué observar:** Primer envío: 200. Repetido/vencido: 400. Scope incorrecto: 403.

**Captura:** [ver imagen](capturas/09_replay.png).

## 10. Duplicar cobros o reembolsos

**Vulnerabilidad:** Repetir una operación para generar efectos financieros duplicados.

**Defensa:** Idempotencia, referencias únicas y transacciones de estado.

```bash
.venv/bin/python scripts/demo_case.py cobros
```

**Qué hará:** Repite un evento y una cancelación; verifica un solo cobro y reembolso.

**Qué observar:** Un pago procesado y un único reembolso por orden.

**Captura:** [ver imagen](capturas/10_cobros.png).

## 11. Reservar el mismo cupo a la vez

**Vulnerabilidad:** Crear dos citas sobre el mismo horario mediante una carrera.

**Defensa:** Bloqueo de franja, transacción y restricción única parcial en PostgreSQL.

```bash
.venv/bin/python scripts/demo_case.py concurrencia
```

**Qué hará:** Lanza 100 hilos con usuarios distintos sobre un mismo turno.

**Qué observar:** Una confirmación y 99 conflictos; un solo pago confirmado.

**Captura:** [ver imagen](capturas/11_concurrencia.png).

**Alcance:** Concurrencia real de servicios y PostgreSQL; no son 100 clics manuales.

## 12. Cruzar centros, médicos o seguros

**Vulnerabilidad:** Un actor interno intenta consultar información fuera de su ámbito.

**Defensa:** Filtros por organización, centro, profesional, póliza y beneficiario.

```bash
.venv/bin/python scripts/demo_case.py ambitos
```

**Qué hará:** Prueba una póliza de otro seguro y una cita de otro profesional.

**Qué observar:** Recurso ajeno: 403. Acceso propio permitido.

**Captura:** [ver imagen](capturas/12_ambitos.png).

## 13. Escalar privilegios

**Vulnerabilidad:** Recepción intenta usar funciones de operador o autoaprobar un rol.

**Defensa:** Permiso por función, dos operadores distintos y revocación de sesiones.

```bash
.venv/bin/python scripts/demo_case.py roles
```

**Qué hará:** Intenta elevar permisos y aprobar el propio pedido; después usa otro operador.

**Qué observar:** Acción no autorizada: 403. El cambio válido exige al segundo operador.

**Captura:** [ver imagen](capturas/13_roles.png).

## 14. Representación falsa de un menor

**Vulnerabilidad:** Reservar para un dependiente sin acreditar representación.

**Defensa:** Solicitud con evidencia y revisión independiente antes de habilitar reservas.

```bash
.venv/bin/python scripts/demo_case.py menores
```

**Qué hará:** Prueba sin evidencia, sin revisión y después con vínculo validado.

**Qué observar:** Sin evidencia no se crea el vínculo; sin revisión no se reserva.

**Captura:** [ver imagen](capturas/14_menores.png).

**Alcance:** La revisión usa evidencia ficticia; no acredita parentesco legal real.

## 15. Reutilizar una sesión revocada

**Vulnerabilidad:** Volver a entrar con una cookie después de salir o tras su expiración.

**Defensa:** Sesión de servidor revocable y fecha de caducidad.

```bash
.venv/bin/python scripts/demo_case.py sesion
```

**Qué hará:** Reutiliza la cookie antigua y prueba otra sesión con fecha ya vencida.

**Qué observar:** El panel devuelve 302 hacia login; no se recupera el acceso.

**Captura:** [ver imagen](capturas/15_sesion.png).

**Alcance:** Una cookie robada aún vigente conserva riesgo de uso.

## 16. Alterar la auditoría

**Vulnerabilidad:** Modificar acciones registradas o dejar cambios sin responsable.

**Defensa:** Actores individuales, cadena HMAC y trigger append-only.

```bash
.venv/bin/python scripts/demo_case.py auditoria
```

**Qué hará:** Registra dos actores, verifica la cadena e intenta modificar un evento.

**Qué observar:** Actores distintos, cadena íntegra y UPDATE rechazado.

**Captura:** [ver imagen](capturas/16_auditoria.png).

**Alcance:** No demuestra resistencia a un administrador total del host y las claves.

## 17. Exponer claves y contraseñas

**Vulnerabilidad:** Publicar secretos reales en código o en archivos con permisos amplios.

**Defensa:** Secretos separados, archivos privados y exclusión de Git.

```bash
.venv/bin/python scripts/demo_case.py secretos
```

**Qué hará:** Revisa permisos y busca valores secretos en fuentes sin mostrarlos.

**Qué observar:** Sin coincidencias de secretos reales en las fuentes revisadas.

**Captura:** [ver imagen](capturas/17_secretos.png).

**Alcance:** Escaneo local acotado; no sustituye Vault ni una auditoría de todo el host.

## 18. Exponer datos sensibles de más

**Vulnerabilidad:** Guardar clínica o tarjetas, o revelar datos médicos en un aviso.

**Defensa:** Minimización, póliza cifrada y plantilla neutral de notificación.

```bash
.venv/bin/python scripts/demo_case.py privacidad
```

**Qué hará:** Inspecciona el esquema, el cifrado de póliza y el texto de un aviso real.

**Qué observar:** Sin campos clínicos/PAN/CVV y aviso sin diagnóstico ni póliza.

**Captura:** [ver imagen](capturas/18_privacidad.png).

## 19. Conservar datos fuera de plazo

**Vulnerabilidad:** Mantener identificable una cuenta vencida o borrar datos con retención legal.

**Defensa:** Disociación por plazo, legal hold y registro de supresiones.

```bash
.venv/bin/python scripts/demo_case.py retencion
```

**Qué hará:** Vence dos cuentas ficticias; una tiene retención legal y la otra no.

**Qué observar:** La cuenta vencida se disocia; la cuenta bajo retención se conserva.

**Captura:** [ver imagen](capturas/19_retencion.png).

## 20. Pérdida o corrupción de la base

**Vulnerabilidad:** Perder las citas y no poder recuperar una copia utilizable.

**Defensa:** Copia cifrada, restauración en otra base y verificación de integridad.

```bash
.venv/bin/python scripts/demo_case.py backup
```

**Qué hará:** Crea una cita sintética, hace backup y restaura en una base NUEVA de Docker.

**Qué observar:** Checksum y auditoría válidos; cita y pago restaurados; sesiones revocadas.

**Captura:** [ver imagen](capturas/20_backup.png).

**Alcance:** Ensayo local; no simula pérdida del host ni demuestra alta disponibilidad.