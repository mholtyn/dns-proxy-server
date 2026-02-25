import socket

from helpers import (
    Header,
    Question,
    ResourceRecord,
    encode_header,
    encode_question,
    encode_record,
    parse_header,
    parse_question,
)

# hard coded answer (for now)
RESPONSE_ANSWER_TTL = 4
RESPONSE_ANSWER_RDATA = b"\x08\x08\x08\x08"


def main():
    print("Logs from your program will appear here!")

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("127.0.0.1", 2053))

    while True:
        try:
            buf, source = udp_socket.recvfrom(512)

            # Request
            parsed_header, offset = parse_header(buf)
            questions: list[Question] = []
            for _ in range(parsed_header.qdcount):
                q, offset = parse_question(buf, offset)
                questions.append(q)

            # Response: same questions but uncompressed + 1 a for each q
            response_header = Header(
                id=parsed_header.id,
                qdcount=len(questions),
                ancount=len(questions),
            )
            response_body = b""
            for q in questions:
                response_body += encode_question(q)
            for q in questions:
                response_body += encode_record(
                    ResourceRecord(
                        name=q.name,
                        type=q.type,
                        class_=q.class_,
                        ttl=RESPONSE_ANSWER_TTL,
                        rdlength=4,
                        rdata=RESPONSE_ANSWER_RDATA,
                    )
                )

            response_packet = encode_header(response_header) + response_body

            udp_socket.sendto(response_packet, source)
        except Exception as e:
            print(f"Error receiving data: {e}")
            break

if __name__ == "__main__":
    main()