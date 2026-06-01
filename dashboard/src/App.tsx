import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { AnomaliesPage } from './pages/AnomaliesPage';
import { DashboardPage } from './pages/DashboardPage';
import { FunnelPage } from './pages/FunnelPage';
import { HeatmapPage } from './pages/HeatmapPage';
import { SystemHealthPage } from './pages/SystemHealthPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="heatmap" element={<HeatmapPage />} />
          <Route path="funnel" element={<FunnelPage />} />
          <Route path="anomalies" element={<AnomaliesPage />} />
          <Route path="health" element={<SystemHealthPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
