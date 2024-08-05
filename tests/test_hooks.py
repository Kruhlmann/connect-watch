from contextlib import closing
import os
import socket
import threading
from typing import Optional

from connect_watch.main import tick


class TcpServer:
    def __init__(self, port: int) -> None:
        self.host: str = "localhost"
        self.port: int = port
        self.running: bool = False
        self.server_socket: Optional[socket.socket] = None
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self) -> None:  # noqa: WPS231
        while self.running:
            try:  # noqa: WPS229
                if self.server_socket is None:
                    continue
                client_socket, _ = self.server_socket.accept()
                if client_socket:
                    client_socket.send(b"ACK")
                    client_socket.shutdown(socket.SHUT_RDWR)
                    client_socket.close()
                    self.stop()
            except BaseException:  # noqa: WPS424,B036
                break

    def stop(self) -> None:
        self.running = False
        if self.server_socket:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temp_socket:
                    temp_socket.connect((self.host, self.port))
                    temp_socket.shutdown(socket.SHUT_RDWR)
            except Exception:  # noqa: S110
                pass  # noqa: WPS420
            self.server_socket.close()

        if self.thread:
            self.thread.join(timeout=1)


def find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("", 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.getsockname()[1]


def test_up() -> None:
    if os.path.exists("./tests/hooks/run.up"):
        os.remove("./tests/hooks/run.up")
    free_port = find_free_port()
    server = TcpServer(port=free_port)
    server.start()

    tick(
        hooks_dir="./tests/hooks",
        hosts_list=[f"localhost:{free_port}"],
        last_state=False,
    )

    assert os.path.isfile("./tests/hooks/run.up")


def test_down() -> None:
    if os.path.exists("./tests/hooks/run.down"):
        os.remove("./tests/hooks/run.down")
    free_port = find_free_port()
    tick(
        hooks_dir="./tests/hooks",
        hosts_list=[f"localhost:{free_port}"],
        last_state=True,
    )

    assert os.path.isfile("./tests/hooks/run.down")
