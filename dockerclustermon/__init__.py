"""dockerclustermon - A CLI tool for a live view of your docker containers running on a remote server."""

__version__ = '0.2.2'
__author__ = 'Michael Kennedy <michael@talkpython.fm>'
__all__ = []

import datetime
import re
import subprocess
import time
from subprocess import CalledProcessError
from threading import Thread
from typing import Annotated, Callable, Tuple

# noinspection PyPackageRequirements
import rich.console

# noinspection PyPackageRequirements
import rich.live

# noinspection PyPackageRequirements
import rich.table
import typer

# noinspection PyPackageRequirements
from rich.text import Text

results = {
    'ps': [],
    'stat': [],
    'free': (0.0, 0.0, 0.0001),
    'error': None,
}
workers = []

__host_type = Annotated[
    str,
    typer.Argument(help='The server DNS name or IP address (e.g. 91.7.5.1 or google.com).'),
]
__user_type = Annotated[
    str,
    typer.Argument(help='The username of the ssh user for interacting with the server.'),
]
__no_ssh = Annotated[
    bool,
    typer.Option('--no-ssh', help='Pass this flag to run locally instead of through ssh.'),
]


def live_status(host: __host_type = 'localhost', username: __user_type = 'root', no_ssh: __no_ssh = False):
    try:
        print()
        if host == 'version':
            print(f'dockerclustermon monitoring utility version {__version__}.')
            return

        if host in {'localhost', '127.0.0.1', '::1'}:
            no_ssh = True

        table = build_table(username, host, no_ssh)
        if not table:
            return

        with rich.live.Live(table, auto_refresh=False) as live:
            while True:
                table = build_table(username, host, no_ssh)
                live.update(table)
                live.refresh()
    except KeyboardInterrupt:
        for w in workers:
            w.join()
        print('kthxbye!')


def process_results():
    ps_lines: list[dict[str, str]] = results['ps']
    stat_lines: list[dict[str, str]] = results['stat']
    total, used, avail = results['free']
    joined = join_results(ps_lines, stat_lines)
    reduced = reduce_lines(joined)
    total_cpu = total_percent(reduced, 'CPU')
    total_mem = total_sizes(reduced, 'Mem')
    return reduced, total, total_cpu, total_mem, used


def run_update(username: str, host: str, no_ssh: bool):
    global workers

    workers.clear()
    workers.append(Thread(target=lambda: run_stat_command(username, host, no_ssh), daemon=True))
    workers.append(Thread(target=lambda: run_ps_command(username, host, no_ssh), daemon=True))
    workers.append(Thread(target=lambda: run_free_command(username, host, no_ssh), daemon=True))

    for w in workers:
        w.start()
    for w in workers:
        w.join()

    if results['error']:
        raise results['error']


def build_table(username: str, host: str, no_ssh: bool):
    # Keys: 'Name', 'Created', 'Status', 'CPU', 'Mem', 'Mem %', 'Limit'
    formatted_date = datetime.datetime.now().strftime('%b %d, %Y @ %I:%M %p')
    table = rich.table.Table(title=f'Docker cluster {host} status {formatted_date}')

    table.add_column('Name', style='white', no_wrap=True)
    # table.add_column("Created",  style="white", no_wrap=True)
    table.add_column('Status', style='green', no_wrap=True)
    table.add_column('CPU %', justify='right', style='white')
    table.add_column('Mem %', justify='right', style='white')
    table.add_column('Mem', justify='right', style='white')
    table.add_column('Limit', justify='right', style='white')
    # noinspection PyBroadException
    try:
        run_update(username, host, no_ssh)
        reduced, total, total_cpu, total_mem, used = process_results()
    except CalledProcessError as cpe:
        print(f'Error: {cpe}')
        return None
    except Exception as x:
        table.add_row('Error', str(x), '', '', '', '')
        time.sleep(1)
        return table

    for container in reduced:
        table.add_row(
            Text(container['Name'], style='bold'),
            color_text(
                container['Status'],
                lambda t: not any(w in t for w in {'unhealthy', 'restart'}),
            ),
            color_number(container['CPU'], low=5, mid=25),
            color_number(container['Mem %'], low=25, mid=65),
            container['Mem'],
            container['Limit'],
        )

    table.add_row()
    table.add_row('Totals', '', f'{total_cpu:,.0f} %', '', f'{total_mem:,.2f} GB', '')
    table.add_row()

    total_server_mem_pct = used / total * 100
    table.add_row(
        'Server',
        '',
        '',
        f'{total_server_mem_pct:,.0f} %',
        f'{used:,.2f} GB',
        f'{total:,.2f} GB',
    )
    return table


def color_number(text: str, low: int, mid: int) -> Text:
    num_text = text.replace('%', '').replace('GB', '').replace('MB', '').replace('KB', '')
    num = float(num_text)

    if num <= low:
        return Text(text, style='green')

    if num <= mid:
        return Text(text, style='cyan')

    return Text(text, style='red')


def color_text(text: str, good: Callable) -> Text:
    if good(text):
        return Text(text)

    return Text(text, style='bold red')


def run_free_command(username: str, host: str, no_ssh: bool) -> Tuple[float, float, float]:
    try:
        # print("Starting free")
        # Run the program and capture its output
        if no_ssh:
            output = subprocess.check_output(['free', '-m'])
        else:
            output = subprocess.check_output(['ssh', f'{username}@{host}', 'free -m'])

        # Convert the output to a string
        output_string = bytes.decode(output, 'utf-8')

        # Convert the string to individual lines
        lines = [line.strip() for line in output_string.split('\n') if line and line.strip()]

        # total        used        free      shared  buff/cache   available
        # Mem:            7937        4257         242         160        3436        3211
        mem_line = lines[1]
        while '  ' in mem_line:
            mem_line = mem_line.replace('  ', ' ')

        parts = mem_line.split(' ')
        used = int(parts[2]) / 1024
        avail = int(parts[5]) / 1024
        total = int(parts[1]) / 1024

        t = total, used, avail
        results['free'] = t

        # print("Free done")

        return t
    except Exception as x:
        msg = str(x)
        if 'No such file or directory: \'free\'' in msg:
            results['error'] = None
            t = 0.001, 0, 0
            results['free'] = t
            return t

        results['error'] = x


def total_sizes(rows: list[dict[str, str]], key: str) -> float:
    # e.g. 1.5GB, 1.5MB, 1.5KB
    total = 0
    for row in rows:
        value = row[key]
        if 'GB' in value:
            value = float(value.replace('GB', ''))
        elif 'MB' in value:
            value = float(value.replace('MB', ''))
            value = value / 1024
        elif 'KB' in value:
            value = float(value.replace('KB', ''))
            value = value / 1024 / 1024
        total += value

    return total


def total_percent(rows: list[dict[str, str]], key: str) -> float:
    # e.g. 50.88%
    total = 0
    for row in rows:
        value = float(row[key].replace('%', ''))
        total += value

    return total


def reduce_lines(joined: list[dict[str, str]]) -> list[dict[str, str]]:
    new_lines = []
    # keep_keys = { 'NAME', 'CREATED', 'STATUS', 'CPU %', 'MEM USAGE / LIMIT', 'MEM %'}

    for j in joined:
        j = split_mem(j)
        reduced = {
            'Name': j['NAME'],
            'Created': j['CREATED'],
            'Status': j['STATUS'],
            'CPU': str(int(float(j['CPU %'].replace('%', '')))) + ' %',
            'Mem': j['MEM USAGE'].replace('KB', ' KB').replace('MB', ' MB').replace('GB', ' GB').replace('  ', ' '),
            'Mem %': str(int(float(j['MEM %'].replace('%', '')))) + ' %',
            'Limit': j['MEM LIMIT'].replace('KB', ' KB').replace('MB', ' MB').replace('GB', ' GB').replace('  ', ' '),
        }
        new_lines.append(reduced)

    # Sort by uptime (youngest first), then by name.
    new_lines.sort(
        key=lambda d: (
            get_seconds_key_from_string(d.get('Status', '')),
            d.get('Name', '').lower().strip(),
        )
    )

    return new_lines


def split_mem(j: dict) -> dict:
    key = 'MEM USAGE / LIMIT'
    # Example: 781.5MiB / 1.5GiB
    value = j[key]
    parts = [v.strip() for v in value.split('/')]

    j['MEM USAGE'] = parts[0].replace('iB', 'B')
    j['MEM LIMIT'] = parts[1].replace('iB', 'B')

    return j


def join_results(ps_lines, stat_lines) -> list[dict[str, str]]:
    join_on = 'NAME'

    joined_lines = []
    ps_dict: dict[str, str]
    stat_lines: dict[str, str]

    for ps_dict, stat_dict in zip(ps_lines, stat_lines):
        # noinspection PyTypeChecker
        if ps_dict[join_on] != stat_dict[join_on]:
            raise Exception('Lines do not match')

        joined = ps_dict.copy()
        # noinspection PyArgumentList
        joined.update(**stat_dict)

        joined_lines.append(joined)

    return joined_lines


def run_stat_command(username: str, host: str, no_ssh: bool) -> list[dict[str, str]]:
    # noinspection PyBroadException
    try:
        # print("Starring stat")
        # Run the program and capture its output
        if no_ssh:
            output = subprocess.check_output(['docker', 'stats', '--no-stream'])
        else:
            output = subprocess.check_output(['ssh', f'{username}@{host}', 'docker stats --no-stream'])

        # Convert the output to a string
        output_string = bytes.decode(output, 'utf-8')

        # Convert the string to individual lines
        lines = [line.strip() for line in output_string.split('\n') if line and line.strip()]

        header = parse_stat_header(lines[0])
        # print(header)

        entries = []
        for line in lines[1:]:
            entries.append(parse_line(line, header))

        results['stat'] = entries

        # print("Done with stat")
        return entries
    except CalledProcessError as e:
        results['error'] = e
    except Exception as x:
        results['error'] = x


def parse_free_header(header_text: str) -> list[Tuple[str, int]]:
    names = ['system', 'used', 'free', 'shared', 'buff/cache', 'available']
    positions = []
    for n in names:
        idx = header_text.index(n)
        item = (n, idx)
        positions.append(item)

    return positions


def parse_stat_header(header_text: str) -> list[Tuple[str, int]]:
    names = [
        'CONTAINER ID',
        'NAME',
        'CPU %',
        'MEM USAGE / LIMIT',
        'MEM %',
        'NET I/O',
        'BLOCK I/O',
        'PIDS',
    ]
    positions = []
    for n in names:
        idx = header_text.index(n)
        item = (n, idx)
        positions.append(item)

    return positions


def run_ps_command(username: str, host: str, no_ssh: bool) -> list[dict[str, str]]:
    try:
        # print("Starting ps ...")
        # Run the program and capture its output
        if no_ssh:
            output = subprocess.check_output(['docker', 'ps'])
        else:
            output = subprocess.check_output(['ssh', f'{username}@{host}', 'docker ps'])

        # Convert the output to a string
        output_string = bytes.decode(output, 'utf-8')

        # Convert the string to individual lines
        lines = [line.strip() for line in output_string.split('\n') if line and line.strip()]

        header = parse_ps_header(lines[0])
        # print(header)

        entries = []
        for line in lines[1:]:
            entries.append(parse_line(line, header))

        results['ps'] = entries
        # print("Done with ps")
        return entries
    except Exception as x:
        results['error'] = x


def parse_line(line: str, header: list[Tuple[str, int]]) -> dict[str, str]:
    local_results = {}
    tmp_headers = header + [('END', 100000)]
    total_len = 0
    for (name, idx), (_, next_idx) in zip(tmp_headers[:-1], tmp_headers[1:]):
        total_len += idx

        # print("Going from {} to {}".format(idx, next_idx))
        value = line[idx:next_idx].strip()
        # print(name + ' -> ' + value)
        if name == 'NAMES':
            name = 'NAME'
        local_results[name] = value

    return local_results


def parse_ps_header(header_text: str) -> list[Tuple[str, int]]:
    names = ['CONTAINER ID', 'IMAGE', 'COMMAND', 'CREATED', 'STATUS', 'PORTS', 'NAMES']
    positions = []
    for n in names:
        idx = header_text.index(n)
        item = (n, idx)
        positions.append(item)

    return positions


def get_seconds_key_from_string(uptime_str: str) -> int:
    if match := re.search(r'(\d+) second', uptime_str):
        dt = int(match.group(1))
        return dt

    if re.search(r'About a minute', uptime_str):
        return 60

    if match := re.search(r'(\d+) minute', uptime_str):
        dt = int(match.group(1))
        return dt * 60

    if re.search(r'About an hour', uptime_str):
        return 60 * 60

    if match := re.search(r'(\d+) hour', uptime_str):
        dt = int(match.group(1))
        return dt * 60 * 60

    if re.search(r'About a day', uptime_str):
        return 60 * 60 * 24

    if match := re.search(r'(\d+) day', uptime_str):
        dt = int(match.group(1))
        return dt * 60 * 60 * 24

    return 1_000_000


def run_live_status():
    typer.run(live_status)


if __name__ == '__main__':
    run_live_status()
