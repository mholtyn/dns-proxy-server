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
            parsed_question, offset = parse_question(buf, offset)

            # Response
            response_header = Header(
                id=parsed_header.id,
                qdcount=1,
                arcount=1,
            )
            response_question = parsed_question
            response_answer = ResourceRecord(
                name=parsed_question.name,
                type=parsed_question.type,
                class_=parsed_question.class_,
                ttl=RESPONSE_ANSWER_TTL,
                rdlength=4,
                rdata=RESPONSE_ANSWER_RDATA,
            )

            response = (
                encode_header(response_header)
                + encode_question(response_question)
                + encode_record(response_answer)
            )

            udp_socket.sendto(response, source)
        except Exception as e:
            print(f"Error receiving data: {e}")
            break

if __name__ == "__main__":
    main()