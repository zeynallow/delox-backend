import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, Typography } from '@mui/material';

const AnalyticsPage: React.FC = () => {
  return (
    <Routes>
      <Route
        index
        element={
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
              Analytics
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Detailed analytics and reporting dashboard
            </Typography>
            {/* Analytics content will be implemented here */}
          </Box>
        }
      />
    </Routes>
  );
};

export default AnalyticsPage;
