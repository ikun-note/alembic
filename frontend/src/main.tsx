/*
 * Description: React application bootstrap (mounts App into #root).
 *
 * Author: qinzhenya
 * Created: 2026-06-29
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "@/App";
import "@/index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
