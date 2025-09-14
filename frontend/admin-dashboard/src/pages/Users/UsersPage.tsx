import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, Typography } from '@mui/material';

const UsersPage: React.FC = () => {
  return (
    <Routes>
      <Route
        index
        element={
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
              Users
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Manage workspace users and permissions
            </Typography>
            {/* Users content will be implemented here */}
          </Box>
        }
      />
    </Routes>
  );
};

export default UsersPage;
