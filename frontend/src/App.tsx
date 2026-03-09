import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Requirements from "./pages/Requirements";
import Controls from "./pages/Controls";
import ReleaseGates from "./pages/ReleaseGates";
import Traceability from "./pages/Traceability";
import IncidentsExceptions from "./pages/IncidentsExceptions";
import AuditExport from "./pages/AuditExport";
import SupplyChain from "./pages/SupplyChain";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="requirements" element={<Requirements />} />
          <Route path="controls" element={<Controls />} />
          <Route path="supply-chain" element={<SupplyChain />} />
          <Route path="release-gates" element={<ReleaseGates />} />
          <Route path="traceability" element={<Traceability />} />
          <Route path="incidents" element={<IncidentsExceptions />} />
          <Route path="audit" element={<AuditExport />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
