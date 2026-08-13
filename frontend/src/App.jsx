import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/auth/Login";
import Dashboard from "./pages/Dashboard";
import Vehicles from "./pages/vehicles/Vehicles";
import LiveTracking from "./pages/vehicles/LiveTracking";
import Drivers from "./pages/drivers/Drivers";
import Shipments from "./pages/shipments/Shipments";
import Trips from "./pages/trips/Trips";
import Maintenance from "./pages/maintenance/Maintenance";
import FuelRecords from "./pages/fuel/FuelRecords";
import Notifications from "./pages/notifications/Notifications";
import Attendance from "./pages/attendance/Attendance";

export default function App() {
  return (
    <Routes>
      {/* AUTH */}
      <Route path="/login" element={<Login />} />

      {/* DASHBOARD */}
      <Route path="/dashboard" element={<Dashboard />} />

      {/* VEHICLES */}
      <Route path="/vehicles" element={<Vehicles />} />
      <Route path="/live-tracking" element={<LiveTracking />} />

      {/* DRIVERS */}
      <Route path="/drivers" element={<Drivers />} />

      {/* SHIPMENTS */}
      <Route path="/shipments" element={<Shipments />} />

      {/* TRIPS */}
      <Route path="/trips" element={<Trips />} />

      {/* MAINTENANCE */}
      <Route path="/maintenance" element={<Maintenance />} />

      {/* FUEL */}
      <Route path="/fuel" element={<FuelRecords />} />

      {/* NOTIFICATIONS */}
      <Route path="/notifications" element={<Notifications />} />

      {/* ATTENDANCE */}
      <Route path="/attendance" element={<Attendance />} />

      {/* ROOT & FALLBACK */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
