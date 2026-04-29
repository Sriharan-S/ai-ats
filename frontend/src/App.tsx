/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Routes, Route, BrowserRouter } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import HomePage from "./pages/HomePage";
import TrackPage from "./pages/TrackPage";
import AtsPage from "./pages/AtsPage";
import LearnPage from "./pages/LearnPage";
import RoadmapDetailPage from "./pages/RoadmapDetailPage";
import PrivacyPage from "./pages/PrivacyPage";
import ContactPage from "./pages/ContactPage";
import SettingsPage from "./pages/SettingsPage";
import { ThemeProvider } from "./contexts/ThemeContext";

export default function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="app-theme">
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<HomePage />} />
          <Route path="track" element={<TrackPage />} />
          <Route path="ats" element={<AtsPage />} />
          <Route path="learn" element={<LearnPage />} />
          <Route path="learn/:slug" element={<RoadmapDetailPage />} />
          <Route path="privacy" element={<PrivacyPage />} />
          <Route path="contact" element={<ContactPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </ThemeProvider>
  );
}
