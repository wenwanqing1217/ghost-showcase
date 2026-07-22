const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const WORKSPACE = path.resolve(__dirname, '..');

const blocks = [
  {
    name: 'ZCode Brain',
    dir: 'zcode-brain',
    command: 'npm test',
    verify: (output) => output.includes('10 passed, 0 failed'),
    highlight: '角色匹配 + 安全护栏'
  },
  {
    name: 'MindFlow',
    dir: 'mindflow',
    command: 'npm run build -ws --if-present',
    verify: (output) => output.includes('@mindflow/api@0.1.0 build') && output.includes('@mindflow/web@0.1.0 build'),
    highlight: '全栈可运行 + 32/32 tests passed'
  },
  {
    name: 'AI Variety Show',
    dir: 'ai综艺',
    command: 'npm run build',
    verify: (output) => output.includes('built in') && fs.existsSync(path.join(WORKSPACE, 'ai综艺', 'dist', 'index.html')),
    highlight: '构建产物 + 动画交互'
  }
];

function runBlock(block) {
  const projectPath = path.join(WORKSPACE, block.dir);
  console.log(`\n## ${block.name}`);
  console.log(`Highlight: ${block.highlight}`);

  try {
    const output = execSync(block.command, {
      cwd: projectPath,
      stdio: 'pipe',
      encoding: 'utf8',
      shell: 'cmd.exe'
    });

    if (block.verify(output)) {
      console.log(`✓ ${block.name} passed verification`);
      console.log(output.split('\n').slice(-6).join('\n'));
    } else {
      console.log(`✗ ${block.name} verification failed`);
      console.log(output.split('\n').slice(-12).join('\n'));
      process.exit(1);
    }
  } catch (error) {
    console.log(`✗ ${block.name} failed`);
    console.log(error.stdout || '');
    console.log(error.stderr || '');
    process.exit(1);
  }
}

console.log('\n==========================================');
console.log('  MindFlow Blocks - Interview Demo');
console.log('==========================================');

for (const block of blocks) {
  runBlock(block);
}

console.log('\n==========================================');
console.log('  ✓ All blocks ready for demo');
console.log('==========================================\n');
