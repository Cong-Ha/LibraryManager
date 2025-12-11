import React from 'react';
import ReactDOM from 'react-dom/client';
import GraphComponent from './GraphComponent';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <GraphComponent />
  </React.StrictMode>
);
