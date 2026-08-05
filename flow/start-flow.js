const { spawn } = require('child_process');
const path = require('path');

const projectRoot = path.resolve(__dirname, 'apps/api');
const tsxBin = path.resolve(__dirname, 'node_modules/.bin/tsx');

const child = spawn(tsxBin, ['src/index.ts'], {
  cwd: projectRoot,
  stdio: 'inherit',
  env: { ...process.env, NODE_ENV: 'development', PORT: '3036', HOST: '127.0.0.1' },
});

child.on('exit', (code) => {
  process.exit(code);
});
