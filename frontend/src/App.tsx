import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import {
  AppLayout,
  SideNavigation,
  type SideNavigationProps,
  Box,
  SpaceBetween,
} from '@cloudscape-design/components';
import ProcessingPage from './pages/ProcessingPage';
import ConfigPage from './pages/ConfigPage';
import LogsPage from './pages/LogsPage';
import OutputPage from './pages/OutputPage';
import HelpPage from './pages/HelpPage';
import DocsPage from './pages/DocsPage';
import es from './i18n/es';

const NAV_ITEMS: SideNavigationProps.Item[] = [
  { type: 'link', text: es.nav.processing, href: '/' },
  { type: 'link', text: 'Archivos ofuscados', href: '/output' },
  { type: 'divider' },
  { type: 'link', text: es.nav.logs, href: '/logs' },
  { type: 'link', text: 'Documentación', href: '/docs' },
  { type: 'link', text: 'Ayuda', href: '/help' },
  { type: 'link', text: es.nav.config, href: '/config' },
];

const AppContent: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [navOpen, setNavOpen] = useState(true);

  const handleNavFollow = (event: CustomEvent<SideNavigationProps.FollowDetail>) => {
    event.preventDefault();
    navigate(event.detail.href);
  };

  return (
    <AppLayout
      navigation={
        <>
          <Box padding={{ horizontal: 'l', top: 'l', bottom: 's' }}>
            <SpaceBetween size="xxxs">
              <Box variant="h2" color="text-status-info">DataMask</Box>
              <Box variant="small" color="text-body-secondary">Enmascarar datos sensibles</Box>
              <Box fontSize="body-s" color="text-status-inactive">v1.0 — by EduTheCoder</Box>
            </SpaceBetween>
          </Box>
          <SideNavigation
            items={NAV_ITEMS}
            activeHref={location.pathname}
            onFollow={handleNavFollow}
          />
        </>
      }
      navigationOpen={navOpen}
      onNavigationChange={({ detail }) => setNavOpen(detail.open)}
      content={
        <Routes>
          <Route path="/" element={<ProcessingPage />} />
          <Route path="/config" element={<ConfigPage />} />
          <Route path="/output" element={<OutputPage />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/docs" element={<DocsPage />} />
          <Route path="/help" element={<HelpPage />} />
        </Routes>
      }
      toolsHide
    />
  );
};

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
};

export default App;
