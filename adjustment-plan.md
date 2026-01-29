# Plan de Ajustes para el Proyecto Houlak CLI

## Objetivo
Implementar un conjunto de ajustes y correcciones en el proyecto para mejorar la claridad de los comandos relacionados con los perfiles del AWS CLI y resolver problemas específicos reportados por los usuarios.

---

## Cambios Propuestos

### 1. Renombrar Comandos Relacionados con Configuración
#### Justificación
Hacer explícito que los comandos `config` y `config-current` están orientados a la configuración de perfiles de AWS CLI y que estos no son necesarios si ya están configurados.

#### Tareas
- Cambiar el comando `config` a `confi-aws-profile` o un nombre similar.
- Cambiar el comando `config-current` a `config-current-profile` o un nombre similar.

---

### 2. Actualizar el `help` de la Aplicación
#### Justificación
Los usuarios deben comprender claramente el propósito de estos comandos y saber que pueden usar sus perfiles de AWS CLI existentes si ya están configurados.

#### Tareas
- Asegurar que las descripciones en el `help` de `confi-aws-profile` y `config-current-profile` sean precisas y expliquen claramente su propósito.
- Ejemplo sugerido para `help`: "Estos comandos son para configurar o mostrar el perfil actual del AWS CLI usado por `houlak-cli`. Si ya tienes tus perfiles configurados, puedes simplemente usarlos."

---

### 3. Actualizar el `README.md`
#### Justificación
Proveer una guía clara y detallada para el uso de los perfiles de AWS CLI, eliminando cualquier duda sobre su propósito y uso.

#### Tareas
- Explicar que los perfiles de AWS pueden configurarse usando los comandos de `houlak-cli` o directamente en el AWS CLI.
- Agregar ejemplos claros de cómo usar perfiles ya configurados en comandos.
- Explicar los pasos para configurar los perfiles mediante `aws configure` y `houlak-cli confi-aws-profile`.

---

### 4. Solucionar el Error en `config-current`
#### Justificación
Actualmente, el comando `config-current` falla con el siguiente error:
```python
AttributeError: 'function' object has no attribute 'show'
```
Este issue impide que los usuarios visualicen la configuración del perfil actual.

#### Tareas
- Revisar la función `config.show()` y corregir el error.
- Es posible que `config` no esté correctamente importado o instanciado como un objeto.
- Escribir o ajustar las pruebas unitarias para validar este caso.

---

### 5. Corregir Error en `db-connect`
#### Contexto
En algunos casos, al ejecutar el comando `houlak-cli db-connect -d hk-postgres-dev`, se muestra el error:
```
tunnel process ended with code 255
```
Este error ocurre luego de una conexión exitosa y sin intervención del usuario.

#### Tareas
- Revisar cómo se maneja la conexión en el código y qué dispara el proceso finalizado con el código 255.
- Investigar posibles problemas de permisos, archivos de configuración mal formados, o fallas en los túneles SSH.
- Asegurar que el proceso SSH utilizado para tunelización maneje adecuadamente errores y excepciones.
- Escribir pruebas para validar casos en los cuales el túnel pueda finalizar abruptamente.

---

## Entregables
- Comandos actualizados (`confi-aws-profile`, `config-current-profile`) correctamente implementados.
- Archivos de ayuda (`help`) explicativos y precisos.
- Archivo `README.md` revisado y mejorado.
- Corrección de errores en los comandos `config-current` y `db-connect`, con pruebas unitarias que aseguren la resolución.

## Pasos Siguientes
1. Priorizar tareas críticas (p.ej., errores en comandos).
2. Desarrollar e implementar los ajustes necesarios.
3. Validar cambios mediante pruebas unitarias y funcionales.
4. Realizar revisiones de código (code review).
5. Publicar nuevas versiones del proyecto tras confirmar los cambios.