#!/usr/bin/env python3
"""Traceroute IPv4/UDP: datagramas manuales y recepción ICMP con RAW sockets."""
import argparse
import math
import secrets
import socket
import struct
import sys
import time

BASE_PORT = 33434
PAYLOAD = b"CCVIII traceroute".ljust(24, b"\x00")


def checksum(data):
    """Complemento a uno de la suma de palabras de 16 bits en orden de red."""
    if len(data) % 2:
        data += b"\x00"
    total = sum(struct.unpack(f"!{len(data) // 2}H", data))
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def build_probe(source, destination, source_port, destination_port, ttl, ident):
    """20 bytes IPv4 + 8 bytes UDP + 24 bytes de datos: 52 bytes."""
    src, dst = socket.inet_aton(source), socket.inet_aton(destination)
    udp_length = 8 + len(PAYLOAD)
    udp = struct.pack("!HHHH", source_port, destination_port, udp_length, 0)
    pseudoheader = src + dst + struct.pack("!BBH", 0, socket.IPPROTO_UDP, udp_length)
    udp_sum = checksum(pseudoheader + udp + PAYLOAD) or 0xFFFF
    udp = struct.pack("!HHHH", source_port, destination_port, udp_length, udp_sum)
    ip = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 20 + udp_length, ident,
                     0, ttl, socket.IPPROTO_UDP, 0, src, dst)
    ip = ip[:10] + struct.pack("!H", checksum(ip)) + ip[12:]
    return ip + udp + PAYLOAD


def ip_header_length(packet, offset=0):
    """IHL real, incluyendo opciones; rechaza cabeceras truncadas."""
    if len(packet) < offset + 20 or packet[offset] >> 4 != 4:
        return None
    length = (packet[offset] & 0x0F) * 4
    return length if length >= 20 and len(packet) >= offset + length else None


def parse_reply(packet, source, destination, source_port, destination_port):
    """Retorna (IP emisor, tipo, código) solo para el probe pendiente.

    El error ICMP contiene 8 bytes de cabecera, la cabecera IPv4 original
    y al menos los primeros 8 bytes de datos originales (cabecera UDP).
    """
    outer = ip_header_length(packet)
    if outer is None or packet[9] != socket.IPPROTO_ICMP:
        return None
    total = struct.unpack_from("!H", packet, 2)[0]
    if total < outer + 8 or total > len(packet):
        return None
    packet = packet[:total]
    if packet[16:20] != socket.inet_aton(source):
        return None
    icmp = packet[outer:]
    if checksum(icmp) != 0:
        return None
    kind, code = icmp[:2]
    if not ((kind == 11 and code == 0) or kind == 3):
        return None
    quoted = outer + 8
    inner = ip_header_length(packet, quoted)
    if inner is None or packet[quoted + 9] != socket.IPPROTO_UDP:
        return None
    if struct.unpack_from("!H", packet, quoted + 6)[0] & 0x1FFF:
        return None  # Un fragmento posterior no comienza con cabecera UDP.
    udp_offset = quoted + inner
    if len(packet) < udp_offset + 8:
        return None
    if packet[quoted + 12:quoted + 16] != socket.inet_aton(source):
        return None
    if packet[quoted + 16:quoted + 20] != socket.inet_aton(destination):
        return None
    sport, dport, length, _ = struct.unpack_from("!HHHH", packet, udp_offset)
    if (sport, dport, length) != (source_port, destination_port, 8 + len(PAYLOAD)):
        return None
    return socket.inet_ntoa(packet[12:16]), kind, code


def wait_reply(receiver, source, destination, source_port, destination_port,
               sent_at, timeout):
    deadline = sent_at + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        receiver.settimeout(remaining)
        try:
            packet, _ = receiver.recvfrom(65535)
        except socket.timeout:
            return None
        received_at = time.monotonic()
        reply = parse_reply(packet, source, destination, source_port, destination_port)
        if reply is not None:
            return (*reply, (received_at - sent_at) * 1000)
        # ICMP ajenos o tardíos no reinician el timeout.


def node_label(address, numeric, cache):
    if numeric:
        return address
    if address not in cache:
        try:
            cache[address] = socket.gethostbyaddr(address)[0]
        except OSError:
            cache[address] = address
    name = cache[address]
    return f"{name} ({address})" if name != address else f"{address} ({address})"


def trace(args):
    destination = socket.gethostbyname(args.destination)
    cache = {}
    # Solo consulta la ruta y reserva el puerto origen; connect() no envía.
    # Los probes se construyen manualmente y se envían exclusivamente por RAW.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as route:
        route.connect((destination, BASE_PORT))
        source, source_port = route.getsockname()
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as receiver, \
             socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW) as sender:
            receiver.bind((source, 0))
            sender.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            print(f"traceroute to {args.destination} ({destination}), "
                  f"{args.max_hops} hops max, 52 byte packets", flush=True)
            index = 0
            ident = secrets.randbelow(65535) + 1
            for ttl in range(args.first_ttl, args.max_hops + 1):
                print(f"{ttl:2d} ", end="", flush=True)
                last_node = None
                reached = unreachable = False
                for _ in range(args.probes):
                    if index:
                        time.sleep(args.pause_ms / 1000)
                    port = BASE_PORT + index
                    packet = build_probe(source, destination, source_port, port,
                                         ttl, (ident + index) % 65535 + 1)
                    sent_at = time.monotonic()
                    sender.sendto(packet, (destination, 0))
                    reply = wait_reply(receiver, source, destination, source_port,
                                       port, sent_at, args.timeout)
                    index += 1
                    if reply is None:
                        print(" *", end="", flush=True)
                        continue
                    address, kind, code, elapsed = reply
                    if address != last_node:
                        print(f" {node_label(address, args.numeric, cache)}", end="", flush=True)
                        last_node = address
                    print(f"  {elapsed:.3f} ms", end="", flush=True)
                    if kind == 3:
                        if code == 3 and address == destination:
                            reached = True
                        else:
                            marker = {0: "!N", 1: "!H", 2: "!P", 3: "!U", 4: "!F",
                                      9: "!X", 10: "!X", 13: "!X"}.get(code, f"!{code}")
                            print(f" {marker}", end="", flush=True)
                            unreachable = True
                print(flush=True)
                # Completa los probes del salto antes de terminar.
                if reached:
                    return 0
                if unreachable:
                    print("Destino no alcanzado: ICMP Destination Unreachable.", file=sys.stderr)
                    return 1
    print("Destino no alcanzado dentro del límite de saltos.", file=sys.stderr)
    return 1


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("debe ser un entero mayor que cero")
    return number


def finite_number(value):
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("debe ser un número finito no negativo")
    return number


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", help="hostname o dirección IPv4 destino")
    parser.add_argument("-f", "--first-ttl", type=positive_int, default=1,
                        help="TTL inicial (por defecto: 1)")
    parser.add_argument("-m", "--max-hops", type=positive_int, default=64,
                        help="TTL máximo/salto final (por defecto: 64)")
    parser.add_argument("-q", "--probes", type=positive_int, default=3,
                        help="probes por salto (por defecto: 3)")
    parser.add_argument("-w", "--timeout", type=finite_number, default=3.0,
                        help="espera por probe en segundos (por defecto: 3)")
    parser.add_argument("-z", "--pause-ms", type=finite_number, default=100.0,
                        help="pausa entre probes en milisegundos (por defecto: 100)")
    parser.add_argument("-n", "--numeric", action="store_true", help="mostrar IP sin DNS inverso")
    args = parser.parse_args(argv)
    if not 1 <= args.first_ttl <= args.max_hops <= 255:
        parser.error("se requiere 1 <= TTL inicial <= máximo de saltos <= 255")
    if args.timeout == 0:
        parser.error("el timeout debe ser mayor que cero")
    if (args.max_hops - args.first_ttl + 1) * args.probes > 65536 - BASE_PORT:
        parser.error("demasiados probes: no hay suficientes puertos UDP únicos")
    return args


def main():
    args = parse_args()
    if not sys.platform.startswith("linux"):
        print("Este programa requiere Linux/Ubuntu y sockets RAW IPv4.", file=sys.stderr)
        return 2
    try:
        return trace(args)
    except PermissionError:
        print("Permiso denegado para RAW sockets. Ejecute: sudo python3 traceroute.py DESTINO",
              file=sys.stderr)
    except OSError as error:
        print(f"Error de red/DNS: {error}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nInterrumpido.", file=sys.stderr)
        return 130
    return 2


if __name__ == "__main__":
    sys.exit(main())
