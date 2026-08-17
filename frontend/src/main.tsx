import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import Bootstrap from "./Bootstrap";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Bootstrap>
      <App />
    </Bootstrap>
  </React.StrictMode>
);
