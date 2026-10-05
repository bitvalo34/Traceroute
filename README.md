# Proyecto #02 - Traceroute

Ciencias de la Computación VIII. Implementación básica en **Python 3**, según
`Proyecto_-_Traceroute.pdf`. Construye manualmente paquetes IPv4/UDP, los envía
con RAW sockets y procesa respuestas ICMP para descubrir la ruta. Usa únicamente
la biblioteca estándar; no ejecuta traceroute ni utiliza Scapy o NetPacket.

## Preparación y ejecución

Requiere Linux/Ubuntu, Python 3.8 o posterior, conectividad IPv4 y permisos para
RAW sockets. No necesita compilación, pip, paquetes Python ni entorno virtual.

```bash
# Solo si no están instalados; traceroute se usa exclusivamente para comparar.
sudo apt-get update
sudo apt-get install python3 traceroute

# Desde la carpeta del proyecto:
sudo python3 traceroute.py galileo.edu
python3 traceroute.py --help
```

Linux exige privilegios de root o la capacidad `CAP_NET_RAW` para abrir
`SOCK_RAW`; por eso se utiliza sudo. No es necesario modificar permisos del
intérprete Python. En Windows, ejecutar el programa dentro de Ubuntu/WSL, no
con el Python de Windows.

## Sintaxis y parámetros

```text
sudo python3 traceroute.py [-f TTL] [-m SALTO_FINAL] [-q PROBES]
                          [-w SEGUNDOS] [-z MILISEGUNDOS] [-n] DESTINO
```

| Argumento | Función | Valor por defecto |
| --- | --- | --- |
| `DESTINO` | Nombre DNS o dirección IPv4 | Obligatorio |
| `-f`, `--first-ttl` | TTL inicial | **1** |
| `-m`, `--max-hops` | TTL máximo, último salto permitido | **64** |
| `-q`, `--probes` | Probes por salto | **3** |
| `-w`, `--timeout` | Espera máxima por probe, en segundos | **3** |
| `-z`, `--pause-ms` | Pausa entre probes, en milisegundos | **100** |
| `-n`, `--numeric` | Desactiva DNS inverso | Desactivado |
| `-h`, `--help` | Muestra ayuda | - |

Se requiere `1 <= TTL inicial <= salto final <= 255`, probes enteros positivos,
timeout finito mayor que cero y pausa finita no negativa. Cada probe usa un
puerto UDP destino único: el total solicitado no puede exceder 32102 probes.
Como en traceroute tradicional, `-f 2 -m 5` recorre los TTL 2, 3, 4 y 5.
El timeout es solo la espera ICMP: DNS puede añadir tiempo a la ejecución.
La pausa se aplica después del probe anterior y antes del siguiente, también
entre saltos; no se agrega una pausa final.

```bash
sudo python3 traceroute.py 1.1.1.1
sudo python3 traceroute.py -n -f 2 -m 12 -q 2 -w 0.5 -z 25 galileo.edu
sudo python3 traceroute.py localhost
```

La salida muestra `salto -> hostname (IP) -> tiempo de cada probe en ms o *`.
Si cambia el router entre probes, se muestra el nuevo hostname/IP en la misma
fila. Sin DNS se conserva la IP. Un `*` significa que ese probe no recibió una
respuesta válida dentro del timeout; no demuestra por sí solo que el router
esté caído. Puede haber filtros, pérdidas o limitación de respuestas ICMP.

Códigos de salida: **0** destino alcanzado, **1** límite de saltos o destino
inaccesible, **2** argumentos/permisos/error de red o DNS, **130** interrupción.
Los errores Destination Unreachable ajenos a la llegada se marcan, por ejemplo,
`!N` red inaccesible, `!H` host inaccesible, `!F` fragmentación necesaria,
`!X` filtrado administrativo o `!U` puerto inaccesible desde otro nodo.

## Funcionamiento a nivel de paquetes

1. Resuelve el destino a IPv4. Un socket UDP auxiliar, sin enviar datos,
   consulta la dirección local que utilizará la ruta y reserva el puerto origen.
2. `build_probe()` arma **52 bytes**: cabecera IPv4 de 20 bytes, UDP de 8 y
   datos de 24. Usa `struct.pack` en orden de red (`!`). Incluye versión/IHL,
   longitud, identificador, TTL, protocolo UDP (17), direcciones, puertos y
   longitudes. Calcula el checksum IPv4 y el UDP mediante complemento a uno;
   el UDP incluye la pseudocabecera IP, que no se transmite como cabecera extra.
3. Envía el datagrama completo por `AF_INET / SOCK_RAW / IPPROTO_RAW` con
   `IP_HDRINCL`. El TTL se escribe directamente en nuestra cabecera IPv4.
   Linux recalcula longitud y checksum IPv4 al enviarlo con `IP_HDRINCL`;
   el programa también los construye y calcula. El checksum UDP es propio.
4. Cada router decrementa el TTL al reenviar. Al expirar, descarta el paquete
   y puede devolver **ICMP Time Exceeded: tipo 11, código 0**. Con TTL 1 se
   identifica el primer router; con TTL 2, el segundo, y así sucesivamente.
5. Recibe por otro socket `AF_INET / SOCK_RAW / IPPROTO_ICMP`. `parse_reply()`
   lee la cabecera IP exterior, verifica el checksum ICMP y examina el paquete
   original citado: IPv4 más los primeros 8 bytes de UDP. Comprueba IP origen,
   IP destino, protocolo y puertos para asociarlo al probe pendiente. Lee el
   IHL real de ambas cabeceras, admite opciones IP y descarta truncamientos,
   respuestas ajenas y respuestas tardías de probes anteriores.
6. La IP exterior identifica al nodo que respondió. El tiempo de ida y vuelta
   se calcula con `time.monotonic()` desde el envío hasta la recepción, antes
   del DNS inverso. Es RTT hasta ese nodo, no el tiempo exclusivo entre routers
   consecutivos, ni necesariamente un trayecto de retorno idéntico al de ida.
7. Al llegar un UDP a un puerto cerrado, el destino responde **ICMP Destination
   Unreachable: tipo 3, código 3 (Port Unreachable)**. Se reconoce la llegada
   solo si el probe coincide y el emisor es la IP destino. Completa los probes
   del salto y termina. Otros códigos de tipo 3 indican fallo, no éxito.

## Pruebas y comparación requerida

Las capturas reales y su interpretación están en [EVIDENCIAS.md](EVIDENCIAS.md).
En la versión pública las IP de los routers están anonimizadas y señaladas;
los destinos, saltos, tiempos y asteriscos se conservan. El ZIP local de entrega
mantiene las capturas originales.
Se verificaron construcción/checksums, ICMP, opciones IP, truncamientos, filtrado,
DNS, valores por defecto, validación de argumentos y timeout absoluto:

```bash
python3 -B tests.py
```

Para repetir las pruebas de red y guardar los dos resultados:

```bash
sudo python3 traceroute.py localhost
sudo python3 traceroute.py -n -f 2 -m 5 -q 2 -w 0.3 -z 250 127.0.0.1

# Mismos destino, protocolo UDP, 52 bytes y parámetros; probes secuenciales.
sudo python3 traceroute.py -n -m 20 -q 3 -w 0.5 -z 100 1.1.1.1 2>&1 | tee propio.log
traceroute -n -N 1 -m 20 -q 3 -w 0.5 -z 0.1 1.1.1.1 52 2>&1 | tee sistema.log

# Repetir con galileo.edu; si DNS elige IP diferentes, comparar la misma IP.
sudo python3 traceroute.py -m 20 -w 0.5 galileo.edu
traceroute -N 1 -m 20 -q 3 -w 0.5 -z 0.1 galileo.edu 52
```

En nuestro programa `-z` siempre está en milisegundos; en el comando Linux,
`-z 0.1` representa 0.1 segundos. `-N 1` evita el envío simultáneo del sistema.
Verificar que ambos observen una secuencia de routers coherente y terminen en
la IP objetivo si la red devuelve Port Unreachable. No se exige igualdad de
RTT, nombres ni todos los probes. Los puertos UDP cambian por probe y pueden
producir balanceo de rutas; también influyen carga, filtros, DNS y hora de prueba.
Un destino puede permanecer sin responder aunque reciba probes; el límite de
saltos evita una ejecución infinita. Con todos los valores por defecto, una
ruta enteramente silenciosa puede tardar unos 10 minutos.

## Entrega

Archivos: `traceroute.py`, `tests.py`, `README.md`, `EVIDENCIAS.md`,
`VIDEO_GUIA.md` y `.gitignore`. La guía contiene el orden de demostración y
respuestas técnicas breves. El PDF exige **código, README y video en un ZIP
por GES**, con evaluación presencial; el video sirve de apoyo si es necesario.
Grabar el video, agregarlo al ZIP del proyecto y subir la entrega al GES.

Referencias auxiliares: [RAW sockets de Linux](https://man7.org/linux/man-pages/man7/raw.7.html)
y [RFC 792: ICMP](https://www.rfc-editor.org/rfc/rfc792.html).
La construcción manual aplica los conceptos de cabeceras, sockets y comunicación
a bajo nivel indicados en el PDF como base del Laboratorio #05.
