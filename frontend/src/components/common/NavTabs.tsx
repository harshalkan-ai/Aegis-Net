import React from 'react';
import { LayoutDashboard, Search, FolderTree, Box, GitFork, ShieldCheck, AlertOctagon, ListOrdered } from 'lucide-react';

export type TabType = 'overview' | 'research' | 'workspace' | 'sandbox' | 'graph' | 'security' | 'incidents' | 'audit';

interface NavTabsProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  openIncidentsCount?: number;
}

interface TabItem {
  id: TabType;
  label: string;
  icon: any;
  badge?: number;
}

export const NavTabs: React.FC<NavTabsProps> = ({ activeTab, setActiveTab, openIncidentsCount = 0 }) => {
  const tabs: TabItem[] = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'research', label: 'Research', icon: Search },
    { id: 'workspace', label: 'Workspace', icon: FolderTree },
    { id: 'sandbox', label: 'Sandbox', icon: Box },
    { id: 'graph', label: 'Agent Graph', icon: GitFork },
    { id: 'security', label: 'Security', icon: ShieldCheck },
    { id: 'incidents', label: 'Incidents', icon: AlertOctagon, badge: openIncidentsCount },
    { id: 'audit', label: 'Audit', icon: ListOrdered },
  ];

  return (
    <nav style={{
      background: 'rgba(5, 10, 20, 0.85)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid rgba(99, 148, 255, 0.1)',
    }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-1 overflow-x-auto py-2" style={{ scrollbarWidth: 'none' }}>
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className="nav-tab"
                style={isActive ? {
                  background: 'rgba(79,142,247,0.12)',
                  borderColor: 'rgba(79,142,247,0.25)',
                  color: '#4f8ef7',
                  fontWeight: 600,
                } : {}}
              >
                <Icon className="w-3.5 h-3.5" style={{ flexShrink: 0 }} />
                <span>{tab.label}</span>
                {!!tab.badge && tab.badge > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold"
                    style={{
                      background: 'rgba(248,113,113,0.15)',
                      border: '1px solid rgba(248,113,113,0.3)',
                      color: '#f87171',
                    }}>
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
