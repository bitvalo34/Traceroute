# Guía rápida para el video

Duración sugerida: 5-7 minutos. Tener abiertas esta carpeta, `traceroute.py` y
una terminal Ubuntu. La demostración debe ser real; las rutas pueden cambiar.

## Orden de grabación

1. **Qué es Traceroute:** descubre progresivamente los routers entre origen y
   destino usando el TTL de IPv4 y respuestas ICMP.
2. **Estructura:** mostrar `checksum`, `build_probe`, `parse_reply`, `wait_reply`,
   `trace` y `parse_args`. Un archivo principal, biblioteca estándar de Python.
3. **RAW sockets:** en `trace`, señalar el emisor `SOCK_RAW/IPPROTO_RAW`,
   `IP_HDRINCL` y receptor `SOCK_RAW/IPPROTO_ICMP`. Explicar por qué se usa sudo.
   El socket UDP auxiliar solo consulta la ruta/reserva el puerto; no envía.
4. **Probe:** mostrar `build_probe`: IPv4 20 bytes + UDP 8 + datos 24 = 52.
   Señalar TTL, protocolo 17, IP origen/destino, puertos y ambos checksums.
5. **TTL:** mostrar el bucle desde el TTL inicial hasta el máximo. Cada router
   decrementa TTL; al expirar descarta el probe, sin reenviarlo.
6. **Time Exceeded:** tipo 11/código 0. Mostrar el análisis de la cabecera
   exterior y del IP/UDP original citado para identificar el probe correcto.
7. **Destino:** tipo 3/código 3 desde la IP objetivo: llegó a un puerto UDP
   cerrado. No confundir otros Destination Unreachable con éxito.
8. **Parámetros:** mostrar ayuda y decir defaults: 1, 64, 3, 3 s, 100 ms.
9. **Demostración real:** ejecutar los comandos siguientes; señalar hop,
   hostname/IP, RTT y asteriscos. Cambiar parámetros sin editar el código.
10. **Comparación Linux:** mostrar ambas salidas para 1.1.1.1 con UDP y los
    mismos parámetros. Consultar `EVIDENCIAS.md` como respaldo de las pruebas.
11. **Diferencias:** explicar tiempos, probes silenciosos y rutas balanceadas.
    Para nombres con varias IP, comparar también una misma IP destino.

```bash
python3 -B tests.py
python3 traceroute.py --help
sudo python3 traceroute.py localhost
sudo python3 traceroute.py -n -f 2 -m 5 -q 2 -w 0.3 -z 250 127.0.0.1
sudo python3 traceroute.py -n -m 20 -q 3 -w 0.5 -z 100 1.1.1.1
traceroute -n -N 1 -m 20 -q 3 -w 0.5 -z 0.1 1.1.1.1 52
```

## Preguntas probables

- **¿Qué viaja en la red?** Ethernet encapsula nuestro IPv4; IPv4 contiene UDP
  y datos. ARP/Ethernet y la transmisión de enlace los maneja el sistema.
  De regreso llega otro IPv4 con ICMP y una cita del IPv4/UDP que enviamos.
- **¿Cómo relacionas el ICMP con un probe?** Leo las IP y los puertos del UDP
  citado; cada probe tiene un puerto destino diferente. Una respuesta de otro
  probe no cuenta ni reinicia la espera.
- **¿Qué construyes tú?** Los bytes IPv4/UDP, TTL y checksums; también analizo
  ICMP. Linux puede recalcular longitud/checksum IP con `IP_HDRINCL`, pero
  las cabeceras ya están construidas por nuestro código; UDP es propio.
- **¿Qué es el checksum UDP?** Complemento a uno sobre pseudocabecera IP,
  cabecera UDP y datos. La pseudocabecera participa en el cálculo, no se envía
  como una cabecera adicional. `!` en struct usa orden de bytes de red.
- **¿TTL es tiempo en segundos?** En este uso es el límite de saltos: cada
  router lo decrementa al reenviar. Impide que un paquete circule indefinidamente.
- **¿Por qué Time Exceeded no significa que llegaste?** Solo confirma que
  expiró TTL. La llegada exige Port Unreachable del destino para nuestro probe.
- **¿Por qué UDP si recibes ICMP?** UDP es el probe; ICMP informa los errores
  de tránsito o de entrega de ese datagrama. Son protocolos distintos sobre IP.
- **¿Un * prueba que el router está caído?** No: puede filtrar o limitar ICMP,
  perder paquetes o tardar más que el timeout. Se continúa con el siguiente TTL.
- **¿Qué mide el tiempo?** RTT desde antes del envío hasta recibir ICMP,
  usando reloj monotónico. No es la latencia exclusiva de ese enlace.
- **¿Por qué varias IP en un salto?** Los probes pueden usar rutas distintas
  por balanceo. El número de hop corresponde al TTL, no a un router fijo.
- **¿Qué pasa si no hay respuesta del destino?** Finaliza al agotar el máximo
  de saltos; no declara éxito. Un puerto abierto podría no enviar Port Unreachable.
- **¿Cómo cambias parámetros durante la evaluación?** Usando `-f`, `-m`, `-q`,
  `-w` y `-z`; mostrar la ayuda y una ejecución con valores distintos.

Al terminar, guardar el video, añadirlo al ZIP y entregar por GES. No afirmar
que las rutas del día de la grabación deben coincidir exactamente con el log.
