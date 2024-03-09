# The Price is Right / El Precio Justo

## Contextualización

Para la segunda evaluación de la asignatura "Programación de Servicios y Procesos" se nos pidió desarrollar, de forma incremental, un juego. En nuestro caso fue el Precio Justo (The Price is Right en Estados Unidos), que fue un concurso que consistía en adivinar, sin pasarse, el precio de objetos cotidianos (y no tan cotidianos).

## Fase I

Desarrollo de la lógica del juego con programación modular, captura de errores y mostrando información de resumen.

## Fase II

Adaptación de la Fase I a un entorno multihilo usando la librería "threads" de Python.

## Fase III

Adaptación de la Fase II a un entorno Cliente-Servidor utilizando sockets orientados a conexión (TCP).

## Fase IV

Adaptación de la Fase III para que la comunicación entre Cliente y Servidor utilice encriptación híbrida (clave simétrica variable en cada comunicación entre pares siendo descifrada con las claves asimétricas correspondientes de cada parte).

# Cómo jugar

Nota: El desarrollo de este juego fue puramente académico, por eso las claves asimétricas privadas están subidas a este repositorio. En un entorno de producción, jamás habría que mostrar nuestra clave privada.

Para jugar necesitaremos tener instalado Python en nuestro ordenador. Aparte, deberemos instalar la librería de PyCryptodome:

```
pip install pycryptodome
```

Podemos descargar todos los archivos (hacen falta los seis) o clonar directamente el directorio con git:

```
git clone https://github.com/frarlo/the-price-is-right.git
```

Para jugar, primero ejecutaremos la instancia de servidor:

```
python servidor.py
```

Y luego la de cliente:
```
python cliente.py
```

### Licencia

Este proyecto está licenciado bajo la Licencia Pública General de GNU (GPL) 3.0.
