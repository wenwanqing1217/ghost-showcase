import os, sys, json, time, logging, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger('collector-daemon')

GATEWAY = os.getenv('GATEWAY_URL', 'http://localhost:18080')
AID = os.getenv('DEFAULT_ALPHA_ID', 'Alpha-001')
POLL = int(os.getenv('COLLECTOR_POLL_INTERVAL', '120'))
# 项目根目录：优先环境变量，回退到当前工作目录（不再硬编码 D:\MW）
PROJECT_DIR = Path(os.getenv('CODE_RUNNER_DIR', os.getcwd()))

STATE_DIR = Path.home() / '.ghost_collectors'
STATE_DIR.mkdir(parents=True, exist_ok=True)


class CollectorRunner:
    def __init__(self, name, detect_fn, collect_fn):
        self.name = name
        self.detect = detect_fn
        self.collect = collect_fn
        self.state = {'last_sync': 0, 'count': 0}
        sf = STATE_DIR / (name + '.json')
        if sf.exists():
            try: self.state.update(json.loads(sf.read_text(encoding='utf-8')))
            except: pass
        self._sf = sf

    def save(self):
        self._sf.write_text(json.dumps(self.state, ensure_ascii=False), encoding='utf-8')

    def run(self):
        try:
            if not self.detect(): return False
            result = self.collect()
            if not result: return False
            self.state['last_sync'] = int(time.time())
            self.state['count'] += 1
            self.save()
            logger.info('[%s] done (#%d)', self.name, self.state['count'])
            return True
        except Exception as e:
            logger.warning('[%s] error: %s', self.name, e)
            return False


def sync_to_gateway(content, category='profile_auto', tags=None):
    try:
        import requests
        tags = tags or ['profile', 'collector']
        r = requests.post(f'{GATEWAY}/v1/memory/store', json={
            'alpha_id': AID, 'content': content,
            'category': category, 'sensitivity': 20,
            'source': 'collector_daemon', 'tags': tags,
        }, timeout=10)
        return r.json().get('success', False)
    except: return False


# --- Collectors ---

def cursor_check():
    for d in [Path.home() / 'AppData/Roaming/Cursor', Path.home() / '.cursor']:
        if d.exists(): return True
    return False

def cursor_collect():
    for base in [Path.home() / 'AppData/Roaming/Cursor', Path.home() / '.cursor']:
        if not base.exists(): continue
        for f in base.rglob('*.db'):
            try:
                import alpha_id.collectors.cursor as cc
                p = cc.collect(f)
                if p:
                    sync_to_gateway(f'[Cursor] style:{p.persona.communication.tone} tech:{p.persona.technical.primary_languages}', 'profile_cursor')
                    return True
            except: continue
    return False


def trae_check():
    for d in [Path.home() / 'AppData/Roaming/Trae', Path.home() / '.trae']:
        if d.exists(): return True
    return False

def trae_collect():
    for base in [Path.home() / 'AppData/Roaming/Trae', Path.home() / '.trae']:
        if not base.exists(): continue
        try:
            import alpha_id.collectors.trae as tc
            p = tc.collect(base)
            if p:
                sync_to_gateway(f'[Trae] {p.persona.communication.tone} {p.persona.technical.primary_languages}', 'profile_trae')
                return True
        except: continue
    return False


def git_check():
    import subprocess
    try:
        r = subprocess.run(['git', 'log', '--oneline', '-1'], capture_output=True, text=True, timeout=5, cwd=str(PROJECT_DIR))
        return bool(r.stdout.strip())
    except: return False

def git_collect():
    import subprocess
    try:
        r = subprocess.run(['git', 'log', '--since=7.days', '--format=%s|%an|%ad', '--date=short'],
                          capture_output=True, text=True, timeout=10, cwd=str(PROJECT_DIR))
        lines = [l for l in r.stdout.strip().split(chr(10)) if l]
        if not lines: return False
        cnt = min(len(lines), 30)
        sync_to_gateway(f'[Git] {cnt} commits in 7 days', 'git_activity', ['git', 'code'])
        return True
    except: return False


def main():
    runners = []
    if cursor_check(): runners.append(CollectorRunner('cursor', cursor_check, cursor_collect))
    if trae_check(): runners.append(CollectorRunner('trae', trae_check, trae_collect))
    runners.append(CollectorRunner('git', git_check, git_collect))

    logger.info('Ghost Collector Daemon v1.0')
    logger.info('Collectors: %s', ', '.join(r.name for r in runners))

    while True:
        if runners:
            with ThreadPoolExecutor(max_workers=len(runners)) as ex:
                fs = {ex.submit(r.run): r.name for r in runners}
                for f in as_completed(fs):
                    try: f.result()
                    except: pass
        time.sleep(POLL)


if __name__ == '__main__':
    # 将项目 src 目录加入 import 路径（用于直接运行此脚本）
    sys.path.insert(0, str(PROJECT_DIR / 'alphaid' / 'projects' / 'src'))
    main()
