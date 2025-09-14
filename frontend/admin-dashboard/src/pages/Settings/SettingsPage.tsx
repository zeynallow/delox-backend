import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, Typography } from '@mui/material';

const SettingsPage: React.FC = () => {
  return (
    <Routes>
      <Route
        index
        element={
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
              Settings
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Workspace settings and configuration
            </Typography>
            {/* Settings content will be implemented here */}
          </Box>
        }
      />
    </Routes>
  );
};

export default SettingsPage;
