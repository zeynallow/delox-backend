import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Star as StarIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';

import LoadingSpinner from '../../../components/Common/LoadingSpinner';

interface CourierPerformanceProps {
  data?: any[];
  loading?: boolean;
}

const CourierPerformance: React.FC<CourierPerformanceProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <Card sx={{ height: 400 }}>
        <CardContent sx={{ height: '100%' }}>
          <LoadingSpinner />
        </CardContent>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card sx={{ height: 400 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Top Couriers
          </Typography>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: 300,
            }}
          >
            <Typography color="text.secondary">
              No data available
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  const getPerformanceColor = (rating: number) => {
    if (rating >= 4.5) return 'success';
    if (rating >= 4.0) return 'warning';
    return 'error';
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <Card sx={{ height: 400 }}>
      <CardContent>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 3,
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Top Couriers
          </Typography>
          <Typography variant="caption" color="text.secondary">
            This week
          </Typography>
        </Box>

        <List sx={{ maxHeight: 320, overflow: 'auto' }}>
          {data.slice(0, 5).map((courier, index) => (
            <ListItem
              key={courier.id}
              sx={{
                px: 0,
                py: 1.5,
                borderBottom: index < data.length - 1 ? '1px solid #f0f0f0' : 'none',
              }}
            >
              <ListItemAvatar>
                <Avatar
                  sx={{
                    bgcolor: index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? '#cd7f32' : 'primary.main',
                    width: 40,
                    height: 40,
                  }}
                >
                  {index < 3 ? (
                    <Typography variant="body2" sx={{ fontWeight: 700 }}>
                      {index + 1}
                    </Typography>
                  ) : (
                    getInitials(courier.name)
                  )}
                </Avatar>
              </ListItemAvatar>

              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      {courier.name}
                    </Typography>
                    {courier.trend === 'up' && (
                      <TrendingUpIcon sx={{ fontSize: 16, color: 'success.main' }} />
                    )}
                    {courier.trend === 'down' && (
                      <TrendingDownIcon sx={{ fontSize: 16, color: 'error.main' }} />
                    )}
                  </Box>
                }
                secondary={
                  <Box sx={{ mt: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <StarIcon sx={{ fontSize: 14, color: 'warning.main' }} />
                      <Typography variant="caption">
                        {courier.rating.toFixed(1)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        • {courier.deliveries} deliveries
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={courier.success_rate}
                        sx={{
                          flexGrow: 1,
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: 'grey.200',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: courier.success_rate >= 90 ? 'success.main' : 
                                           courier.success_rate >= 80 ? 'warning.main' : 'error.main',
                          },
                        }}
                      />
                      <Typography variant="caption" sx={{ minWidth: 35 }}>
                        {courier.success_rate}%
                      </Typography>
                    </Box>
                  </Box>
                }
              />

              <Box sx={{ textAlign: 'right' }}>
                <Chip
                  label={`${courier.rating.toFixed(1)}`}
                  size="small"
                  color={getPerformanceColor(courier.rating) as any}
                  variant="outlined"
                />
              </Box>
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

export default CourierPerformance;
