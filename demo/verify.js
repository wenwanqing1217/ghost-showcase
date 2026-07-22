const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const WORKSPACE = path.resolve(__dirname, '..');

const projects = [
  {
    name: 'MindFlow',
    dir: 'mindflow',
    buildCheck: 'apps/web/.next/BUILD_ID',
    testCommand: 'npm test',
    demoUrl: 'http://localhost:3000',
    description: 'AI Workflow Platform'
  },
  {
    name: 'DS',
    dir: 'DS',
    buildCheck: '.next/BUILD_ID',
    testCommand: 'npx vitest run',
    demoUrl: 'http://localhost:3000',
    description: 'AI Autonomous Shopify Shop'
  },
  {
    name: 'ai综艺',
    dir: 'ai综艺',
    buildCheck: 'dist/index.html',
    testCommand: null,
    demoUrl: 'http://localhost:5173',
    description: 'AI Variety Show'
  },
  {
    name: 'ZCode Brain',
    dir: 'zcode-brain',
    buildCheck: null,
    testCommand: 'npm test',
    demoUrl: null,
    description: 'Agent Orchestration'
  }
];

console.log('\n==========================================');
console.log('  MindFlow Portfolio - Demo Verification');
console.log('==========================================\n');

let allReady = true;

projects.forEach(project => {
  const projectPath = path.join(WORKSPACE, project.dir);

  console.log(`[${project.name}] ${project.description}`);

  if (project.buildCheck) {
    const buildPath = path.join(projectPath, project.buildCheck);
    if (fs.existsSync(buildPath)) {
      console.log(`  ✓ Build verified`);
    } else {
      console.log(`  ✗ Build not found - run build-all.bat first`);
      allReady = false;
    }
  }

  if (project.testCommand) {
    try {
      console.log(`  Running tests...`);
      const output = execSync(project.testCommand, {
        cwd: projectPath,
        stdio: ['pipe','pipe','pipe'],
        encoding: 'utf8'
      });
      const normalized = output.replace(/\u001b\[[;\d]*m/g, '');
      const matches = normalized.match(/(\d+)\s+passed/g) || [];
      const lastMatch = matches.at(-1);
      if (lastMatch) {
        console.log(`  ✓ ${lastMatch.split(/\s+/)[0]} tests passed`);
      } else {
        console.log(`  ✓ Tests completed`);
      }
    } catch (error) {
      console.log(`  ✗ Tests failed`);
      console.log(`    ${error.message.split('\n')[0]}`);
      allReady = false;
    }
  }

  if (project.demoUrl) {
    console.log(`  Demo: ${project.demoUrl}`);
  }

  console.log('');
});

console.log('==========================================');
if (allReady) {
  console.log('  ✓ All projects ready for demo!');
} else {
  console.log('  ⚠ Some projects need attention.');
  console.log('    Run build-all.bat to build all projects.');
}
console.log('==========================================\n');

console.log('Next steps:');
console.log('  1. Run start-demo.bat to launch projects');
console.log('  2. Open browser to demo URLs');
console.log('  3. Follow PORTFOLIO.md for interview script\n');

process.exit(allReady ? 0 : 1);
