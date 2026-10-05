"""Pruebas del formato de paquetes, filtrado ICMP y argumentos; sin sudo."""
import contextlib
import io
import socket
import struct
import unittest
from unittest.mock import patch
import traceroute as tr

SOURCE, DESTINATION, ROUTER = "192.0.2.10", "198.51.100.20", "192.0.2.1"
SPORT, DPORT = 45000, 33434


def response(kind=11, code=0, port=DPORT, options=False):
    quoted = tr.build_probe(SOURCE, DESTINATION, SPORT, port, 1, 123)[:28]
    if options:
        quoted = bytes([0x46]) + quoted[1:20] + b"\x01\x01\x01\x01" + quoted[20:]
    icmp = struct.pack("!BBHI", kind, code, 0, 0) + quoted
    icmp = icmp[:2] + struct.pack("!H", tr.checksum(icmp)) + icmp[4:]
    sender = DESTINATION if kind == 3 and code == 3 else ROUTER
    extra = b"\x01\x01\x01\x01" if options else b""
    header = struct.pack("!BBHHHBBH4s4s", 0x46 if options else 0x45, 0,
                         20 + len(extra) + len(icmp), 456, 0, 64, 1, 0,
                         socket.inet_aton(sender), socket.inet_aton(SOURCE)) + extra
    header = header[:10] + struct.pack("!H", tr.checksum(header)) + header[12:]
    return header + icmp


class PacketTests(unittest.TestCase):
    def parse(self, packet):
        return tr.parse_reply(packet, SOURCE, DESTINATION, SPORT, DPORT)

    def test_checksum_known_vector_and_odd_length(self):
        self.assertEqual(tr.checksum(bytes.fromhex("0001f203f4f5f6f7")), 0x220D)
        self.assertEqual(tr.checksum(b"\x01\x02\x03"), 0xFBFD)

    def test_manually_built_ip_and_udp(self):
        packet = tr.build_probe(SOURCE, DESTINATION, SPORT, DPORT, 7, 123)
        self.assertEqual(len(packet), 52)
        self.assertEqual(packet[0], 0x45)
        self.assertEqual(packet[8:10], bytes([7, 17]))
        self.assertEqual(struct.unpack_from("!H", packet, 2)[0], 52)
        self.assertEqual(tr.checksum(packet[:20]), 0)
        self.assertEqual(struct.unpack_from("!HHH", packet, 20), (SPORT, DPORT, 32))
        pseudo = packet[12:20] + struct.pack("!BBH", 0, 17, 32)
        self.assertEqual(tr.checksum(pseudo + packet[20:]), 0)
        self.assertNotEqual(packet[26:28], b"\x00\x00")

    def test_ttl_exceeded(self):
        self.assertEqual(self.parse(response()), (ROUTER, 11, 0))

    def test_destination_port_unreachable(self):
        self.assertEqual(self.parse(response(3, 3)), (DESTINATION, 3, 3))

    def test_other_unreachable(self):
        self.assertEqual(self.parse(response(3, 13)), (ROUTER, 3, 13))

    def test_ip_options(self):
        self.assertEqual(self.parse(response(options=True)), (ROUTER, 11, 0))

    def test_unrelated_delayed_probe(self):
        self.assertIsNone(self.parse(response(port=DPORT + 1)))
        self.assertIsNone(tr.parse_reply(response(), SOURCE, DESTINATION, SPORT + 1, DPORT))
        self.assertIsNone(tr.parse_reply(response(), SOURCE, "198.51.100.21", SPORT, DPORT))

    def test_corrupt_or_truncated_packets(self):
        packet = response()
        for length in range(len(packet)):
            self.assertIsNone(self.parse(packet[:length]))
        self.assertIsNone(self.parse(packet[:-1] + bytes([packet[-1] ^ 1])))
        self.assertIsNone(self.parse(bytes([0x65]) + packet[1:]))

    def test_unsupported_icmp(self):
        self.assertIsNone(self.parse(response(11, 1)))
        self.assertIsNone(self.parse(response(8, 0)))

    def test_timeout_is_not_reset_by_foreign_icmp(self):
        class Receiver:
            def settimeout(self, value):
                self.timeout = value
            def recvfrom(self, size):
                return response(port=DPORT + 1), (ROUTER, 0)
        receiver = Receiver()
        with patch.object(tr.time, "monotonic", side_effect=[10.1, 10.2, 10.5]):
            self.assertIsNone(tr.wait_reply(receiver, SOURCE, DESTINATION, SPORT,
                                            DPORT, 10, 0.5))
        self.assertAlmostEqual(receiver.timeout, 0.4)

    def test_dns_fallback_and_cache(self):
        with patch.object(tr.socket, "gethostbyaddr", side_effect=socket.herror):
            self.assertEqual(tr.node_label(ROUTER, False, {}), f"{ROUTER} ({ROUTER})")
        cache = {}
        with patch.object(tr.socket, "gethostbyaddr", return_value=("router.test", [], [])) as dns:
            self.assertEqual(tr.node_label(ROUTER, False, cache), f"router.test ({ROUTER})")
            tr.node_label(ROUTER, False, cache)
            self.assertEqual(dns.call_count, 1)

    def test_default_and_changed_arguments(self):
        args = tr.parse_args(["localhost"])
        self.assertEqual((args.first_ttl, args.max_hops, args.probes, args.timeout,
                          args.pause_ms), (1, 64, 3, 3, 100))
        args = tr.parse_args(["-f", "2", "-m", "5", "-q", "2", "-w", "0.5",
                              "-z", "25", "-n", "localhost"])
        self.assertEqual((args.first_ttl, args.max_hops, args.probes, args.timeout,
                          args.pause_ms, args.numeric), (2, 5, 2, 0.5, 25, True))

    def test_invalid_arguments(self):
        for option in (["-f", "0"], ["-m", "256"], ["-f", "3", "-m", "2"],
                       ["-q", "0"], ["-w", "0"], ["-w", "nan"], ["-z", "-1"],
                       ["-z", "inf"], ["-m", "255", "-q", "1000"]):
            with self.subTest(option=option), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    tr.parse_args(option + ["localhost"])
                self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
