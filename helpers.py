"""

Definiuję format wiadomości DNS (pakiet UDP, nie TCP).

Zasady:
- Dataclassy (Header, Question, ResourceRecord) trzymają tylko "znaczenie":
  liczby jako int, nazwę domeny jako list[str] (np. ["example", "com"]),
  surowe dane rekordu (rdata) jako bytes. Nie ma żadnych gotowych bajtów
  "do wysłania".
- Do tego slużą funkcję encode_*. Odbywa się tam zamiana na bajty (wire format).
  Dzięki temu w jednym miejscu wiadomo, w jakiej kolejności i formacie idzie to
  do sieci.
- Kolejność pól w dataclassach = kolejność w specyfikacji DNS (RFC 1035).
  Rozbijamy wszystko na czynniki piewrsze, żeby łatwo mapować "to pole = ten
  kawałek pakietu".

"""

from dataclasses import dataclass
import struct


@dataclass
class Header:
    id: int
    qr: int = 1
    opcode: int = 0
    aa: int = 0
    tc: int = 0
    rd: int = 0
    ra: int = 0
    z: int = 0
    rcode: int = 0
    qdcount: int = 0
    ancount: int = 0
    nscount: int = 0
    arcount: int = 0


@dataclass
class Question:
    name: list[str]
    type: int = 1
    class_: int = 1


@dataclass
class ResourceRecord:
    name: list[str]
    type: int = 1
    class_: int = 1
    ttl: int
    rdlength: int
    rdata: bytes


def encode_dns_name(labels: list[str]) -> bytes:
    out = []
    for label in labels:
        b: bytes = label.encode("ascii")
        out.append(bytes([len(b)]) + b)
    out.append(b"\x00")
    return b"".join(out)


def decode_dns_name(buf: bytes, start: int) -> tuple[list[str], int]:
    """
    Odczytuje nazwę domeny z buf od start. Obsługuje kompresję: jeśli bajt
    ma bity 11 (wskaźnik), skok pod 14-bitowy offset i odczyt reszty nazwy stamtąd.
    Zwraca (lista etykiet, indeks bajtu ZA nazwą).
    """
    out: list[str] = []
    pos: int = start
    while True:
        length_byte = buf[pos]
        pos += 1
        if length_byte == 0:
            break
        # sprawdzam dwa pierwsze bity bajtu, jesli to 11, to ten bajt 
        # nie mowi o dlugosci labela tylko jest pointerem
        if (length_byte & 0xC0) == 0xC0:
            offset = ((length_byte & 0x3F) << 8) | buf[pos]
            pos += 1
            labels_tail, _ = decode_dns_name(buf, offset)
            out.extend(labels_tail)
            break
        label = buf[pos : pos + length_byte].decode("ascii")
        out.append(label)
        pos += length_byte
    return (out, pos)


def encode_header(h: Header) -> bytes:
    byte1_flags = (h.qr << 7) | (h.opcode << 3) | (h.aa << 2) | (h.tc << 1) | h.rd
    byte2_flags = (h.ra << 7) | (h.z << 4) | h.rcode
    return (
        struct.pack("!H", h.id)
        + struct.pack("!BB", byte1_flags, byte2_flags)
        + struct.pack("!HHHH", h.qdcount, h.ancount, h.nscount, h.arcount)
    )


def encode_question(q: Question) -> bytes:
    return encode_dns_name(q.name) + struct.pack("!HH", q.type, q.class_)


def encode_record(r: ResourceRecord) -> bytes:
    return (
        encode_dns_name(r.name)
        + struct.pack("!HHIH", r.type, r.class_, r.ttl, r.rdlength)
        + r.rdata
    )


def parse_header(buf: bytes) -> tuple[Header, int]:
    """
    Deserialize header content (first 12 bytes).
    Returns tuple(Header, offset=12)
    """

    # 1. check buffer length
    if len(buf) < 12:
        raise ValueError("Incorrect header length!")

    # 2. extract bytes to Header() attributes
    (id,) = struct.unpack("!H", buf[0:2])
    (byte1_flags,) = struct.unpack("!B", buf[2:3])
    (byte2_flags,) = struct.unpack("!B", buf[3:4])

    qr: int = (byte1_flags >> 7) & 0b1
    opcode: int = (byte1_flags >> 3) & 0b1111
    aa: int = (byte1_flags >> 2) & 0b1
    tc: int = (byte1_flags >> 1) & 0b1
    rd: int = byte1_flags & 0b1

    ra: int = (byte2_flags >> 7) & 0b1
    z: int =  (byte2_flags >> 4) & 0b111
    rcode: int = byte2_flags & 0b1111

    qdcount, ancount, nscount, arcount = struct.unpack("!HHHH", buf[4:12])

    # 3. build and return header
    header = Header(
        id=id,
        qr=qr,
        opcode=opcode,
        aa=aa,
        tc=tc,
        rd=rd,
        ra=ra,
        z=z,
        rcode=rcode,
        qdcount=qdcount,
        ancount=ancount,
        nscount=nscount,
        arcount=arcount
    )

    return (header, 12)


def parse_question(buf: bytes, offset: int) -> tuple[Question, int]:
    name, pos = decode_dns_name(buf, offset)
    (type, class_) = struct.unpack("!HH", buf[pos : pos + 4])
    question = Question(name=name, type=type, class_=class_)
    return (question, pos + 4)


def parse_answer(buf: bytes, offset: int) -> tuple[ResourceRecord, int]:
    name, pos = decode_dns_name(buf, offset)
    (rtype, rclass, ttl, rdlength) = struct.unpack("!HHIH", buf[pos : pos + 10])
    rdata = buf[pos + 10 : pos + 10 + rdlength]
    record = ResourceRecord(
        name=name,
        type=rtype,
        class_=rclass,
        ttl=ttl,
        rdlength=rdlength,
        rdata=rdata,
    )
    return (record, pos + 10 + rdlength)
