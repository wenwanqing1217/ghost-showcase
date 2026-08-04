'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { useEffect, useState } from 'react';

export default function WorkflowPage() {
  const [src, setSrc] = useState('/workflow-editor/index.html');

  useEffect(() => {
    // 强制刷新 iframe 以绕过 IAB 缓存的旧重定向
    setSrc(`/workflow-editor/index.html?t=${Date.now()}`);
  }, []);

  return (
    <AuthGuard>
      <TopBar title="工作流" subtitle="Agent 工作流编排与执行" />
      <div style={{ height: 'calc(100vh - 56px)', width: '100%' }}>
        <iframe
          src={src}
          style={{ width: '100%', height: '100%', border: 'none' }}
          title="工作流编辑器"
        />
      </div>
    </AuthGuard>
  );
}
