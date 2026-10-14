import { existsSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const local = fileURLToPath(new URL(process.platform === 'win32'
  ? '../.venv/Scripts/python.exe' : '../.venv/bin/python', import.meta.url));
const executable = process.env.PYTHON || (existsSync(local) ? local : 'python');
const child = spawn(executable, process.argv.slice(2), { cwd: root, stdio: 'inherit' });
child.on('error', error => { console.error(error.message); process.exitCode = 1; });
child.on('exit', code => { process.exitCode = code ?? 1; });
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal));
