import socket
import typer

from helpers import (
    Header,
    Question,
    ResourceRecord,
    encode_header,
    encode_question,
    encode_record,
    parse_answer,
    parse_header,
    parse_question,
)

def main(resolver: str = typer.Option(..., "--resolver", help="Resolver ip:port")):
    ip, port_str = resolver.rsplit(":", 1)
    resolver_addr = (ip, int(port_str))

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(("127.0.0.1", 2053))

    resolver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    resolver_socket.settimeout(15.0)

    while True:
        try:
            buf, source = client_socket.recvfrom(512)

            parsed_header, offset = parse_header(buf)
            questions: list[Question] = []
            for _ in range(parsed_header.qdcount):
                question, offset = parse_question(buf, offset)
                questions.append(question)

            answers: list[ResourceRecord] = []
            for question in questions:
                # rd=1 bo bez tego publiczny resolver zwraca SERVFAIL
                # current project assumption: one question for each packet
                request_packet = encode_header(Header(id=0, qr=0, rd=1, qdcount=1)) + encode_question(question)
                resolver_socket.sendto(request_packet, resolver_addr)
                resolver_response_buffer, _ = resolver_socket.recvfrom(512)
                resolver_response_header, response_offset = parse_header(resolver_response_buffer)
                
                # debug resolver response
                # print("from resolver:", len(resolver_response_buffer), "bytes, ancount:", resolver_response_header.ancount, "qr:", resolver_response_header.qr, "rcode:", resolver_response_header.rcode)
                
                _, response_offset = parse_question(resolver_response_buffer, response_offset)
                for _ in range(resolver_response_header.ancount):
                    resource_record, response_offset = parse_answer(resolver_response_buffer, response_offset)
                    answers.append(resource_record)

            response_header = Header(
                id=parsed_header.id,
                qdcount=len(questions),
                ancount=len(answers),
                arcount=0,
            )
            response_body = b""
            for question in questions:
                response_body += encode_question(question)
            for resource_record in answers:
                response_body += encode_record(resource_record)

            client_socket.sendto(encode_header(response_header) + response_body, source)
        except Exception as e:
            print(f"Error: {e}")
            break


if __name__ == "__main__":
    typer.run(main)