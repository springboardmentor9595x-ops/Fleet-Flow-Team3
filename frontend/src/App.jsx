import { Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import ProtectedRoute from "./routes/ProtectedRoute";
import Vehicles from "./pages/Vehicle";
import VehicleForm from "./pages/VehicleForm";
import Profile from "./pages/Profile";
import VerifyEmail from "./pages/VerifyEmail";
import LiveTracking from "./pages/LiveTracking";
import Shipments from "./pages/Shipments";
import ShipmentForm from "./pages/ShipmentForm";
import ShipmentDetail from "./pages/ShipmentDetail";
import TripList from "./pages/TripList";
import TripScheduler from "./pages/TripScheduler";
import TripDetail from "./pages/TripDetail";
import Drivers from "./pages/Drivers";
import DriverForm from "./pages/DriverForm";
import Maintenance from "./pages/Maintenance";
import FleetAnalytics from "./pages/FleetAnalytics";
import LogisticsAnalytics from "./pages/LogisticsAnalytics";
import AdminAnalytics from "./pages/AdminAnalytics";
import FuelLog from "./pages/FuelLog";
import Reports from "./pages/Reports";

function App() {
  return (
    <Routes>

      <Route
        path="/"
        element={<Navigate to="/login" replace />}
      />

      <Route
        path="/login"
        element={<Login />}
      />

      <Route
        path="/signup"
        element={<Signup />}
      />

      <Route
        path="/verify-email"
        element={<VerifyEmail />}
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      <Route
        path="/vehicles"
        element={
          <ProtectedRoute>
            <Vehicles />
          </ProtectedRoute>
        }
      />

      <Route
        path="/vehicles/add"
        element={
          <ProtectedRoute>
            <VehicleForm />
          </ProtectedRoute>
        }
      />

      <Route
        path="/vehicles/edit/:vehicleId"
        element={
          <ProtectedRoute>
            <VehicleForm />
          </ProtectedRoute>
        }
      />
      <Route path="/shipments" element={<ProtectedRoute><Shipments /></ProtectedRoute>} />
      <Route path="/shipments/add" element={<ProtectedRoute><ShipmentForm /></ProtectedRoute>} />
      <Route path="/shipments/:shipmentId/edit" element={<ProtectedRoute><ShipmentForm /></ProtectedRoute>} />
      <Route path="/shipments/:shipmentId" element={<ProtectedRoute><ShipmentDetail /></ProtectedRoute>} />
      <Route path="/trips" element={<ProtectedRoute><TripList /></ProtectedRoute>} />
      <Route path="/trips/schedule" element={<ProtectedRoute><TripScheduler /></ProtectedRoute>} />
      <Route path="/trips/:tripId" element={<ProtectedRoute><TripDetail /></ProtectedRoute>} />
      <Route path="/drivers" element={<ProtectedRoute><Drivers /></ProtectedRoute>} />
      <Route path="/drivers/new" element={<ProtectedRoute><DriverForm /></ProtectedRoute>} />
      <Route path="/drivers/:driverId/edit" element={<ProtectedRoute><DriverForm /></ProtectedRoute>} />
      <Route path="/maintenance" element={<ProtectedRoute><Maintenance /></ProtectedRoute>} />
      <Route path="/fuel-log" element={<ProtectedRoute allowedRoles={["Admin", "FleetManager", "Dispatcher", "Driver"]}><FuelLog /></ProtectedRoute>} />
      <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
      <Route path="/analytics/fleet" element={<ProtectedRoute allowedRoles={["Admin", "FleetManager"]}><FleetAnalytics /></ProtectedRoute>} />
      <Route path="/analytics/logistics" element={<ProtectedRoute allowedRoles={["Admin", "FleetManager", "Dispatcher"]}><LogisticsAnalytics /></ProtectedRoute>} />
      <Route path="/analytics/admin" element={<ProtectedRoute allowedRoles={["Admin"]}><AdminAnalytics /></ProtectedRoute>} />
      <Route
  path="/live-tracking"
  element={
    <ProtectedRoute>
      <LiveTracking />
    </ProtectedRoute>
  }
/>
      <Route
  path="/profile"
  element={
    <ProtectedRoute>
      <Profile />
    </ProtectedRoute>
  }
/>

    </Routes>
  );
}

export default App;
