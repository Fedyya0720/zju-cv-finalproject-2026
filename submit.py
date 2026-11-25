#!/usr/bin/env python3
"""CV2026 submission client. Python 3.10+ and OpenSSH; no pip dependencies."""
import argparse
from contextlib import contextmanager
import getpass
import io
import json
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess
import sys
import tempfile
import time
import unicodedata
import zipfile

HERE = Path(__file__).resolve().parent
MANIFEST = json.loads((HERE / 'tools/submission.json').read_text(encoding='utf-8'))


def alias_value(value):
    if value is None:
        raise ValueError('每次提交必须显式指定 --alias；不会自动使用历史别名')
    value = unicodedata.normalize('NFC', value.strip())
    if not 2 <= len(value) <= 32 or any(unicodedata.category(c).startswith('C') for c in value):
        raise ValueError('alias 必须为 2–32 个字符且不能包含控制字符')
    if value.casefold() in {'your_alias', 'your alias', 'alias', 'changeme', '你的别名', '请填写别名', '本组选择的别名'}:
        raise ValueError('请填写本组实际 alias，不要保留占位符')
    return value


def pack_images(folder):
    folder = Path(folder)
    if not folder.is_dir():
        raise ValueError(f'图片目录不存在：{folder}')
    items = list(folder.iterdir())
    expected = set(MANIFEST['test_names'])
    if set(p.name for p in items) != expected or len(items) != len(expected):
        missing = sorted(expected - {p.name for p in items})
        extra = sorted({p.name for p in items} - expected)
        raise ValueError(f'目录必须只包含指定的 20 张 PNG；缺少 {missing}；多出 {extra}')
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_STORED) as archive:
        for name in MANIFEST['test_names']:
            path = folder / name
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 4*1024*1024:
                raise ValueError(f'{name}: 需要普通 PNG 文件，每张不超过 4 MiB')
            data = path.read_bytes()
            if len(data) < 26 or data[:8] != b'\x89PNG\r\n\x1a\n':
                raise ValueError(f'{name}: 不是 PNG')
            width, height = struct.unpack('>II', data[16:24])
            if (width, height) != (MANIFEST['width'], MANIFEST['height']) or data[24:26] != b'\x08\x02':
                raise ValueError(f'{name}: 需要 768×432、8-bit RGB PNG（不能带 alpha）')
            archive.writestr(name, data)
    body = output.getvalue()
    if len(body) > 32*1024*1024:
        raise ValueError('总上传量不能超过 32 MiB')
    return body


@contextmanager
def connection(args):
    with tempfile.TemporaryDirectory(prefix='cv-submit-') as folder:
        control = str(Path(folder) / 'ssh')
        options = ['-p', str(args.port), '-o', 'ControlMaster=auto', '-o', 'ControlPersist=60',
                   '-o', 'ControlPath=' + control, '-o', 'ConnectTimeout=15']
        known = HERE / 'tools/ssh/known_hosts'
        if known.exists():
            options += ['-o', 'HostKeyAlias=cv2026-training', '-o', 'UserKnownHostsFile='+str(known),
                        '-o', 'StrictHostKeyChecking=yes']
        if args.ssh_config:
            options = ['-F', str(args.ssh_config)] + options
        target = args.user + '@' + args.host
        def call(action, body=None, **kwargs):
            words = ['/usr/local/bin/cv-submit-gateway', action]
            for key, value in kwargs.items():
                words += ['--' + key, str(value)]
            r = subprocess.run(['ssh', *options, target, shlex.join(words)], input=body,
                               stdout=subprocess.PIPE, stderr=None, timeout=180)
            if r.returncode:
                raise RuntimeError('提交/查询被拒绝或 SSH 连接失败，详见上方错误；已接收任务不会因断线丢失')
            try:
                return json.loads(r.stdout)
            except (ValueError, UnicodeDecodeError):
                raise RuntimeError('服务器返回格式异常，请联系助教')
        try:
            yield call
        finally:
            if Path(control).exists():
                subprocess.run(['ssh', '-S', control, '-O', 'exit', '-p', str(args.port), target],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)


def show(result):
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--images', type=Path, help='仅含固定 20 张预测 RGB PNG 的目录')
    mode.add_argument('--status', help='查询既有 submission_id，不发起新提交')
    p.add_argument('--alias', help='每次新提交必填，首次绑定后不可自行修改')
    p.add_argument('--user', default=getpass.getuser(), help='本组账号，例如 cv26_001')
    p.add_argument('--host', help='默认使用配置好的 cv2026；在训练机本组账号下运行时自动连本机')
    p.add_argument('--port', type=int, default=22)
    p.add_argument('--ssh-config', type=Path, help='可选的 OpenSSH 配置文件，默认使用 ~/.ssh/config')
    p.add_argument('--no-wait', action='store_true', help='接收后退出，之后按编号查询')
    p.add_argument('--check-only', action='store_true', help='仅校验输入，不连接服务器、不绑定 alias')
    a = p.parse_args()
    try:
        body = None
        if a.images is not None:
            a.alias = alias_value(a.alias)  # Mandatory before any file upload or SSH connection.
            body = pack_images(a.images)
        elif a.check_only:
            p.error('--check-only 需要 --images 和 --alias')
        if a.check_only:
            print(f'校验通过：20 张图片，alias={a.alias}，不会发起提交')
            return 0
        if not re.fullmatch(r'cv26_(?:00[1-9]|0[1-9][0-9]|[1-9][0-9]{2})', a.user):
            p.error('请用 --user cv26_XXX 指定本组服务器账号')
        on_training_server = getpass.getuser() == a.user and (Path('/etc/cv2026/credentials')/a.user).is_file()
        a.host = a.host or ('127.0.0.1' if on_training_server else MANIFEST['ssh_host'])
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', a.host) or not 1 <= a.port <= 65535:
            p.error('无效 SSH host/port')
        if a.status and not re.fullmatch('[a-f0-9]{32}', a.status):
            p.error('无效提交编号')
        if a.images is not None:
            print(f'本次 alias：{a.alias}。首次接收后永久绑定；后续每次必须提供相同别名。', flush=True)
        with connection(a) as call:
            if a.status:
                result = call('status', id=a.status)
                show(result)
                return 1 if result['status'] == 'failed' else 0
            result = call('submit', body=body, alias=a.alias)
            show(result)
            identity = result['submission_id']
            if a.no_wait:
                return 0
            deadline = time.monotonic() + 1800
            while time.monotonic() < deadline:
                time.sleep(3)
                result = call('status', id=identity)
                if result['status'] in ('succeeded', 'failed'):
                    show(result)
                    return 0 if result['status'] == 'succeeded' else 1
                print(f"状态：{result['status']}，前方排队 {result['queued_ahead']} 个", flush=True)
            print(f'等待超时，任务仍保留。稍后用 --status {identity} 查询。')
            return 2
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as e:
        print(f'错误：{e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
