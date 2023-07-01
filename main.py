import socket
import threading

def handle_client(client_socket):
    try:
        client_data = client_socket.recv(262)
      
        server_handshake = b"\x05\x00"
        client_socket.send(server_handshake)

        client_request = client_socket.recv(262)

        addr_type = client_request[3]
        if addr_type == 1:  # IPv4
            dest_address = socket.inet_ntoa(client_request[4:8])
            dest_port = int.from_bytes(client_request[8:], byteorder='big')
        elif addr_type == 3:  # domain name
            dest_length = client_request[4]
            dest_address = client_request[5:5+dest_length].decode()
            dest_port = int.from_bytes(client_request[5+dest_length:], byteorder='big')
        else:
            # not supported
            client_socket.close()
            return

        print("[*] Received request to {}:{}".format(dest_address, dest_port))

        # connect to the destination server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((dest_address, dest_port))
        print("[*] Connected to {}:{}".format(dest_address, dest_port))

        server_response = b"\x05\x00\x00\x01" + socket.inet_aton("0.0.0.0") + (8888).to_bytes(2, byteorder='big')
        client_socket.send(server_response)

        relay_data(client_socket, server_socket)
    except (socket.error, ConnectionResetError):
        pass
    finally:
        client_socket.close()
        server_socket.close()

def relay_data(src_socket, dst_socket):
    while True:
        try:
            data = src_socket.recv(4096)
            if len(data) > 0:
                dst_socket.sendall(data)
            else:
                break
        except (socket.error, ConnectionResetError):
            break

    src_socket.close()
    dst_socket.close()

def start_proxy_server():
    proxy_host = '0.0.0.0'  # local
    proxy_port = 8888  # port

    proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server.bind((proxy_host, proxy_port))
    proxy_server.listen(5)

    print("[*] Proxy server started on {}:{}".format(proxy_host, proxy_port))

    while True:
        client_socket, addr = proxy_server.accept()
        print("[*] Accepted connection from {}:{}".format(addr[0], addr[1]))
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

start_proxy_server()
