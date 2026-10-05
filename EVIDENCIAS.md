# Evidencia real de pruebas (direcciones de routers anonimizadas)

**Privacidad:** en esta versión pública, las IP de los routers locales y del
proveedor se sustituyeron consistentemente por direcciones reservadas para
documentación (192.0.2.0/24, 198.51.100.0/24 y 203.0.113.0/24). Estas direcciones
son etiquetas de anonimización, no las IP observadas ni destinos para repetir
la prueba. Se conservan los saltos, RTT, asteriscos, códigos de salida y las
IP públicas de los destinos. Las capturas originales permanecen en el ZIP local
`Traceroute_entrega.zip`, fuera del repositorio público. El programa no contiene
resultados codificados ni aplica esta anonimización a sus ejecuciones.

Fecha: 2026-10-05 (America/Guatemala). Entorno: Ubuntu sobre WSL2.
Los resultados proceden de capturas de ejecuciones; las IP de routers se anonimizaron como se indica arriba.

## Versión de referencia

```console
$ traceroute --version
Modern traceroute for Linux, version 2.1.5
Copyright (c) 2016  Dmitry Butskoy,   License: GPL v2 or any later
```

Código de salida: 0. Duración total: 0.001 s.

## Pruebas automatizadas

```console
$ python3 -B tests.py
test_checksum_known_vector_and_odd_length (__main__.PacketTests.test_checksum_known_vector_and_odd_length) ... ok
test_corrupt_or_truncated_packets (__main__.PacketTests.test_corrupt_or_truncated_packets) ... ok
test_default_and_changed_arguments (__main__.PacketTests.test_default_and_changed_arguments) ... ok
test_destination_port_unreachable (__main__.PacketTests.test_destination_port_unreachable) ... ok
test_dns_fallback_and_cache (__main__.PacketTests.test_dns_fallback_and_cache) ... ok
test_invalid_arguments (__main__.PacketTests.test_invalid_arguments) ... ok
test_ip_options (__main__.PacketTests.test_ip_options) ... ok
test_manually_built_ip_and_udp (__main__.PacketTests.test_manually_built_ip_and_udp) ... ok
test_other_unreachable (__main__.PacketTests.test_other_unreachable) ... ok
test_timeout_is_not_reset_by_foreign_icmp (__main__.PacketTests.test_timeout_is_not_reset_by_foreign_icmp) ... ok
test_ttl_exceeded (__main__.PacketTests.test_ttl_exceeded) ... ok
test_unrelated_delayed_probe (__main__.PacketTests.test_unrelated_delayed_probe) ... ok
test_unsupported_icmp (__main__.PacketTests.test_unsupported_icmp) ... ok

----------------------------------------------------------------------
Ran 13 tests in 0.005s

OK
```

Código de salida: 0. Duración total: 0.102 s.

## Programa propio: valores por defecto y DNS

```console
$ python3 -B traceroute.py localhost
traceroute to localhost (127.0.0.1), 64 hops max, 52 byte packets
 1  localhost (127.0.0.1)  0.147 ms  0.183 ms  0.089 ms
```

Código de salida: 0. Duración total: 0.271 s.

## Sistema: localhost con parámetros equivalentes

```console
$ traceroute -N 1 -m 64 -q 3 -w 3 -z 0.1 localhost 52
traceroute to localhost (127.0.0.1), 64 hops max, 52 byte packets
 1  localhost (127.0.0.1)  1.109 ms  0.607 ms  0.667 ms
```

Código de salida: 0. Duración total: 0.204 s.

## Parámetros modificados: TTL inicial, probes, espera y pausa

```console
$ python3 -B traceroute.py -n -f 2 -m 5 -q 2 -w 0.3 -z 250 127.0.0.1
traceroute to 127.0.0.1 (127.0.0.1), 5 hops max, 52 byte packets
 2  127.0.0.1  0.136 ms  0.096 ms
```

Código de salida: 0. Duración total: 0.306 s.

## Límite de saltos: no confundir router con destino

```console
$ python3 -B traceroute.py -n -m 1 -q 1 -w 0.5 -z 0 1.1.1.1
traceroute to 1.1.1.1 (1.1.1.1), 1 hops max, 52 byte packets
 1  192.0.2.1  7.089 ms
Destino no alcanzado dentro del límite de saltos.
```

Código de salida: 1. Duración total: 0.048 s.

## Programa propio: 1.1.1.1

```console
$ python3 -B traceroute.py -m 20 -w 0.5 1.1.1.1
traceroute to 1.1.1.1 (1.1.1.1), 20 hops max, 52 byte packets
 1  192.0.2.1 (192.0.2.1)  6.860 ms  7.532 ms  7.051 ms
 2  198.51.100.2 (198.51.100.2)  18.366 ms 198.51.100.3 (198.51.100.3)  15.493 ms 198.51.100.2 (198.51.100.2)  17.832 ms
 3  198.51.100.5 (198.51.100.5)  17.140 ms 198.51.100.4 (198.51.100.4)  17.115 ms 198.51.100.5 (198.51.100.5)  16.609 ms
 4  * * *
 5  * * *
 6  * * *
 7  203.0.113.7 (203.0.113.7)  17.103 ms  40.070 ms  28.430 ms
 8  one.one.one.one (1.1.1.1)  18.111 ms  29.700 ms  19.167 ms
```

Código de salida: 0. Duración total: 7.458 s.

## Sistema UDP: 1.1.1.1

```console
$ traceroute -N 1 -m 20 -q 3 -w 0.5 -z 0.1 1.1.1.1 52
traceroute to 1.1.1.1 (1.1.1.1), 20 hops max, 52 byte packets
 1  192.0.2.1 (192.0.2.1)  7.450 ms  7.856 ms  7.895 ms
 2  198.51.100.3 (198.51.100.3)  20.469 ms  15.278 ms 198.51.100.2 (198.51.100.2)  16.907 ms
 3  198.51.100.4 (198.51.100.4)  18.293 ms  17.645 ms 198.51.100.5 (198.51.100.5)  15.781 ms
 4  * * *
 5  * * *
 6  * * *
 7  203.0.113.7 (203.0.113.7)  22.353 ms *  22.354 ms
 8  one.one.one.one (1.1.1.1)  17.817 ms  19.162 ms  17.202 ms
```

Código de salida: 0. Duración total: 6.586 s.

## Programa propio: galileo.edu

```console
$ python3 -B traceroute.py -m 20 -w 0.5 galileo.edu
traceroute to galileo.edu (104.20.20.230), 20 hops max, 52 byte packets
 1  192.0.2.1 (192.0.2.1)  7.423 ms  7.457 ms  7.634 ms
 2  198.51.100.3 (198.51.100.3)  27.153 ms 198.51.100.2 (198.51.100.2)  60.061 ms 198.51.100.3 (198.51.100.3)  71.775 ms
 3  198.51.100.4 (198.51.100.4)  19.476 ms 198.51.100.5 (198.51.100.5)  17.039 ms 198.51.100.4 (198.51.100.4)  16.846 ms
 4  * * *
 5  * * *
 6  * * *
 7  203.0.113.7 (203.0.113.7)  17.715 ms  18.047 ms  19.689 ms
 8  104.20.20.230 (104.20.20.230)  21.128 ms  24.567 ms  17.906 ms
```

Código de salida: 0. Duración total: 7.831 s.

## Sistema UDP: galileo.edu

```console
$ traceroute -N 1 -m 20 -q 3 -w 0.5 -z 0.1 galileo.edu 52
traceroute to galileo.edu (172.66.174.65), 20 hops max, 52 byte packets
 1  192.0.2.1 (192.0.2.1)  7.328 ms  7.358 ms  7.496 ms
 2  198.51.100.3 (198.51.100.3)  15.588 ms 198.51.100.2 (198.51.100.2)  24.564 ms  15.591 ms
 3  198.51.100.4 (198.51.100.4)  17.688 ms 198.51.100.5 (198.51.100.5)  15.383 ms 198.51.100.4 (198.51.100.4)  15.574 ms
 4  * * *
 5  * * *
 6  * * *
 7  203.0.113.7 (203.0.113.7)  33.506 ms  22.377 ms  28.060 ms
 8  172.66.174.65 (172.66.174.65)  17.193 ms  17.428 ms  17.370 ms
```

Código de salida: 0. Duración total: 6.230 s.

## Sistema: misma IP que resolvió el programa para galileo.edu

```console
$ traceroute -N 1 -m 20 -q 3 -w 0.5 -z 0.1 104.20.20.230 52
traceroute to 104.20.20.230 (104.20.20.230), 20 hops max, 52 byte packets
 1  192.0.2.1 (192.0.2.1)  7.554 ms  7.116 ms  7.220 ms
 2  198.51.100.3 (198.51.100.3)  15.489 ms 198.51.100.2 (198.51.100.2)  16.831 ms 198.51.100.3 (198.51.100.3)  16.037 ms
 3  198.51.100.4 (198.51.100.4)  16.986 ms 198.51.100.5 (198.51.100.5)  16.390 ms  16.529 ms
 4  * * *
 5  * * *
 6  * * *
 7  203.0.113.7 (203.0.113.7)  18.235 ms  23.055 ms  18.054 ms
 8  104.20.20.230 (104.20.20.230)  27.594 ms  17.673 ms  21.560 ms
```

Código de salida: 0. Duración total: 6.194 s.

## Timeout y parámetros modificados: dos probes al salto silencioso

```console
$ python3 -B traceroute.py -n -f 4 -m 4 -q 2 -w 0.15 -z 50 1.1.1.1
traceroute to 1.1.1.1 (1.1.1.1), 4 hops max, 52 byte packets
 4  * *
Destino no alcanzado dentro del límite de saltos.
```

Código de salida: 1. Duración total: 0.415 s.

## Error de permisos sin sudo

```console
$ runuser -u erwin -- python3 -B traceroute.py 127.0.0.1
Permiso denegado para RAW sockets. Ejecute: sudo python3 traceroute.py DESTINO
```

Código de salida: 2. Duración total: 0.057 s.

## Error DNS controlado

```console
$ python3 -B traceroute.py does-not-exist.invalid
Error de red/DNS: [Errno -2] Name or service not known
```

Código de salida: 2. Duración total: 0.093 s.

## Interpretación y comprobaciones

- **localhost:** ambos identificaron 127.0.0.1 en el primer salto y tres RTT.
  El programa usó exactamente los defaults 1, 64, 3, 3 s y 100 ms.
- **1.1.1.1:** ambos alcanzaron el destino en 8 saltos. Coinciden el primer
  router 192.0.2.1, los grupos de routers de los saltos 2 y 3, los saltos
  silenciosos 4-6, el router 203.0.113.7 del salto 7 y la IP destino.
- **galileo.edu:** ambos alcanzaron el destino en 8 saltos, pero el DNS eligió
  104.20.20.230 para el programa y 172.66.174.65 para el sistema. El hostname
  puede resolver a varias IP. La comparación adicional del sistema contra
  104.20.20.230 confirma una ruta coherente a la misma IP del programa.
- Las IP alternas de los saltos 2 y 3 son compatibles con balanceo de rutas.
  Los RTT diferentes son normales. El sistema tuvo un probe silencioso adicional
  en el salto 7 hacia 1.1.1.1; pérdida o limitación ICMP son explicaciones
  posibles, no causas demostradas por estos logs.
- `-f 2 -m 5 -q 2 -w 0.3 -z 250` comenzó en el salto 2, mostró dos RTT y
  terminó al alcanzar localhost. Duró 0.306 s, compatible con la pausa de
  250 ms entre los probes.
- `-f 4 -m 4 -w 0.15 -q 2 -z 50` mostró dos asteriscos y tardó 0.415 s:
  al menos 2 x 0.15 s de espera + 0.05 s de pausa, más el arranque del programa.
  Confirma timeout y pausa modificables sobre un salto silencioso real.
- El límite de un salto detuvo la ejecución sin declarar que 192.0.2.1 era
  el destino. Permisos y DNS inválido devolvieron mensajes claros y código 2.
- Las 13 pruebas automatizadas pasaron: checksums, opciones IP, paquetes
  truncados/corruptos, filtrado de respuestas ajenas y valores defaults.

Las pruebas de red sí pudieron ejecutarse. Se usó el usuario root de Ubuntu/WSL
para RAW sockets, pues sudo sin interacción requiere contraseña en esta sesión.
En una terminal normal se ejecuta con sudo. Los resultados son evidencia histórica;
no están codificados en la lógica del programa y las rutas futuras pueden cambiar.
