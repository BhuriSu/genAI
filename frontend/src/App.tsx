import React from 'react';
import MultiCompanyDashboard from './components/MultiCompanyDashboard';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

const theme = createTheme({
  // Customize your theme here
});

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className="min-h-screen bg-gray-100">
        <MultiCompanyDashboard />
      </div>
    </ThemeProvider>
  );
};

export default App;