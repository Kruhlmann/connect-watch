import asyncio
from glob import glob
import os
from socket import gaierror
import subprocess  # noqa: S404
import sys
import time
from typing import Optional

import click


async def check_tcp_connection(host: str, port: str, timeout: int) -> bool:
    try:  # noqa: WPS229
        await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        return True
    except (asyncio.TimeoutError, ConnectionRefusedError, gaierror) as err:
        print(f"Unable to connect to {host}:{port}: {err}")  # noqa: WPS421
        return False
    except BaseException as err:  # noqa: WPS424,B036
        print(f"Unable to connect to {host}:{port}: Generic Exception: {err}")  # noqa: WPS421
        return False


async def check_tcp_connections(hosts: list[tuple[str, str]], timeout: int) -> bool:
    tasks = [check_tcp_connection(host, port, timeout) for (host, port) in hosts]
    return all(await asyncio.gather(*tasks))


def run_hooks(connected: bool, hooks_dir: str) -> None:
    print(f"Running hooks connected={connected}")  # noqa: WPS421
    hooks = glob(f"{hooks_dir}/*.up") if connected else glob(f"{hooks_dir}/*.down")  # noqa: WPS221
    for hook in hooks:
        stdoutput = subprocess.run([hook], stdout=subprocess.PIPE, text=True)  # noqa: S603
        print(stdoutput.stdout)  # noqa: WPS421


def tick(hooks_dir: str, hosts_list: list[str], last_state: Optional[bool]) -> None:  # noqa: WPS210
    hosts_to_check_prepack = [tuple(host.split(":")) for host in hosts_list]
    hosts_to_check: list[tuple[str, str]] = [(host, port) for host, port in hosts_to_check_prepack]
    current_state = asyncio.run(check_tcp_connections(hosts=hosts_to_check, timeout=5))
    if last_state is None:
        last_state = current_state
        return

    if current_state != last_state:
        run_hooks(connected=current_state, hooks_dir=hooks_dir)
        last_state = current_state


@click.command()
@click.version_option()
@click.option("--hooks-dir", "-d", help="Path to hooks directory")
@click.option("--hosts", "-h", help="Comma separated list of hosts to watch")
@click.option("--sleep", "-s", help="Time to wait between each connection attempt (seconds)")
def main(hooks_dir: str, hosts: str, sleep: int) -> None:
    hosts_list = hosts.split(",")
    last_state: Optional[bool] = None

    if not os.path.isdir(hooks_dir):
        print(f"Permission denied: {hooks_dir}")  # noqa: WPS421
        sys.exit(1)

    while True:  # noqa: WPS457
        tick(hooks_dir=hooks_dir, hosts_list=hosts_list, last_state=last_state)
        time.sleep(sleep)


if __name__ == "__main__":
    main()
