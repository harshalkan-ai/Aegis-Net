import React, { useEffect, useState } from 'react';
import { FolderTree, FileText, Folder, RefreshCw, Send, Loader2, FileCode, ChevronRight } from 'lucide-react';
import { workspaceApi } from '../api/workspaceApi';
import { deploymentApi } from '../api/deploymentApi';
import { FileEntry, FileContentResponse } from '../types';

interface WorkspacePageProps {
  activeSessionId: string | null;
  onNavigateToDeployer: () => void;
}

export const WorkspacePage: React.FC<WorkspacePageProps> = ({ activeSessionId, onNavigateToDeployer }) => {
  const [tree, setTree] = useState<FileEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>('README.md');
  const [fileContent, setFileContent] = useState<FileContentResponse | null>(null);
  const [fileLoading, setFileLoading] = useState(false);
  const [deployLoading, setDeployLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTree = async () => {
    if (!activeSessionId) return;
    setLoading(true);
    setError(null);

    try {
      const res = await workspaceApi.getTree(activeSessionId);
      setTree(res.entries || []);
      if (res.entries && res.entries.length > 0 && !selectedFilePath) {
        setSelectedFilePath(res.entries[0].path);
      }
    } catch (err: any) {
      setError(`Workspace fetch error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeSessionId) {
      fetchTree();
    }
  }, [activeSessionId]);

  useEffect(() => {
    if (activeSessionId && selectedFilePath) {
      fetchFileContent(selectedFilePath);
    }
  }, [selectedFilePath, activeSessionId]);

  const fetchFileContent = async (path: string) => {
    if (!activeSessionId) return;
    setFileLoading(true);

    try {
      const res = await workspaceApi.getFileContent(activeSessionId, path);
      setFileContent(res);
    } catch (err: any) {
      setFileContent({
        content: `Error loading file '${path}': ${err.message}`,
        path,
        bytes: 0,
      });
    } finally {
      setFileLoading(false);
    }
  };

  const handleSendToDeployer = async () => {
    if (!activeSessionId) return;
    setDeployLoading(true);

    try {
      await deploymentApi.runDeployer(activeSessionId, fileContent?.content || undefined);
      onNavigateToDeployer();
    } catch (err: any) {
      setError(`Deployer trigger failed: ${err.message}`);
    } finally {
      setDeployLoading(false);
    }
  };

  const renderTreeNodes = (nodes: FileEntry[], depth = 0) => {
    return nodes.map((node) => {
      const isSelected = selectedFilePath === node.path;
      const isDir = node.type === 'dir';

      return (
        <div key={node.path} style={{ paddingLeft: `${depth * 14}px` }}>
          <div
            onClick={() => { if (!isDir) setSelectedFilePath(node.path); }}
            className="flex items-center gap-2 py-1.5 px-2 rounded-lg text-xs cursor-pointer select-none transition"
            style={isSelected && !isDir ? {
              background: 'rgba(79,142,247,0.12)',
              border: '1px solid rgba(79,142,247,0.25)',
              color: '#4f8ef7',
            } : {
              color: '#94a3b8',
              border: '1px solid transparent',
            }}
            onMouseEnter={e => {
              if (!isSelected) {
                (e.currentTarget as HTMLDivElement).style.background = 'rgba(255,255,255,0.04)';
                (e.currentTarget as HTMLDivElement).style.color = '#e2e8f0';
              }
            }}
            onMouseLeave={e => {
              if (!isSelected) {
                (e.currentTarget as HTMLDivElement).style.background = 'transparent';
                (e.currentTarget as HTMLDivElement).style.color = '#94a3b8';
              }
            }}
          >
            {isDir ? (
              <Folder className="w-3.5 h-3.5 shrink-0" style={{ color: '#4f8ef7' }} />
            ) : (
              <FileText className="w-3.5 h-3.5 shrink-0" style={{ color: '#64748b' }} />
            )}
            <span className="truncate">{node.name}</span>
            {!isDir && node.size !== undefined && (
              <span className="text-[10px] font-mono ml-auto" style={{ color: '#334155' }}>
                {node.size}B
              </span>
            )}
          </div>

          {isDir && node.children && node.children.length > 0 && (
            <div className="mt-0.5">
              {renderTreeNodes(node.children, depth + 1)}
            </div>
          )}
        </div>
      );
    });
  };

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div className="glass-card p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'rgba(52,211,153,0.12)', border: '1px solid rgba(52,211,153,0.25)' }}>
            <FolderTree className="w-5 h-5" style={{ color: '#34d399' }} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Workspace Management</h1>
            <p className="text-xs text-slate-500">
              Sandboxed files created by Coder Agent · Session:{' '}
              <code className="font-mono text-slate-300 text-[11px]">{activeSessionId || 'None'}</code>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchTree}
            disabled={loading || !activeSessionId}
            className="btn-ghost"
            style={{ padding: '8px 14px', fontSize: '12px' }}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleSendToDeployer}
            disabled={deployLoading || !activeSessionId}
            className="btn-primary"
            style={{ padding: '8px 16px', fontSize: '12px' }}
          >
            {deployLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Deploying...</span>
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>SEND TO DEPLOYER →</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl text-xs"
          style={{ background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.2)', color: '#f87171' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {!activeSessionId ? (
        <div className="glass-card p-16 text-center space-y-3">
          <FolderTree className="w-12 h-12 mx-auto" style={{ color: '#1e3a5f' }} />
          <p className="font-bold text-white">No active research session selected.</p>
          <p className="text-xs text-slate-500">Start a session in the Research tab to view generated workspace files.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* File Tree Panel */}
          <div className="glass-card p-5 space-y-3">
            <div className="flex items-center justify-between pb-3"
              style={{ borderBottom: '1px solid rgba(99,148,255,0.08)' }}>
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">File Explorer</span>
              <span className="font-mono text-[11px]" style={{ color: '#334155' }}>agent_workspace/</span>
            </div>

            {loading ? (
              <div className="py-10 flex items-center justify-center gap-2 text-slate-500 text-xs">
                <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                <span>Loading workspace...</span>
              </div>
            ) : tree.length === 0 ? (
              <div className="py-10 text-center text-xs text-slate-600">
                No files found. Run Coder Agent to generate files.
              </div>
            ) : (
              <div className="space-y-0.5 overflow-y-auto max-h-[500px] pr-1">
                {renderTreeNodes(tree)}
              </div>
            )}
          </div>

          {/* File Content Viewer */}
          <div className="lg:col-span-2 glass-card p-5 space-y-3 flex flex-col">
            <div className="flex items-center justify-between pb-3"
              style={{ borderBottom: '1px solid rgba(99,148,255,0.08)' }}>
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-blue-400" />
                <span className="font-mono text-xs font-bold text-slate-300">
                  {selectedFilePath || 'No file selected'}
                </span>
              </div>

              {fileContent && (
                <div className="flex items-center gap-3 text-[11px] text-slate-600 font-mono">
                  <span>{fileContent.bytes} bytes</span>
                  {fileContent.modified_at && <span>· {fileContent.modified_at}</span>}
                </div>
              )}
            </div>

            {fileLoading ? (
              <div className="py-20 flex items-center justify-center gap-2 text-slate-500 text-xs">
                <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                <span>Reading file content from sandbox...</span>
              </div>
            ) : fileContent ? (
              <div className="flex-1 overflow-hidden">
                <pre className="terminal-text text-[11px] overflow-x-auto max-h-[520px] overflow-y-auto whitespace-pre-wrap leading-relaxed">
                  {fileContent.content}
                </pre>
              </div>
            ) : (
              <div className="py-20 text-center text-xs text-slate-600">
                Select a file to inspect its content.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
