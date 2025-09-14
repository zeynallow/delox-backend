import React from 'react';
import { Grid, Card, CardContent, Typography, Box, Avatar } from '@mui/material';
import {
  ShoppingCart as OrdersIcon,
  LocalShipping as CouriersIcon,
  AttachMoney as RevenueIcon,
  TrendingUp as PerformanceIcon,
  CheckCircle as CompletedIcon,
  Schedule as PendingIcon,
} from '@mui/icons-material';

import { DashboardStats } from '../../../types';

interface StatsCardsProps {
  stats?: DashboardStats;
}

interface StatCard {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  change?: string;
  changeColor?: string;
}

const StatsCards: React.FC<StatsCardsProps> = ({ stats }) => {
  if (!stats) {
    return null;
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const statCards: StatCard[] = [
    {
      title: 'Total Orders',
      value: stats.total_orders.toLocaleString(),
      icon: <OrdersIcon />,
      color: '#1976d2',
    },
    {
      title: 'Active Orders',
      value: stats.active_orders.toLocaleString(),
      icon: <PendingIcon />,
      color: '#ed6c02',
    },
    {
      title: 'Completed Orders',
      value: stats.completed_orders.toLocaleString(),
      icon: <CompletedIcon />,
      color: '#2e7d32',
    },
    {
      title: 'Active Couriers',
      value: `${stats.active_couriers}/${stats.total_couriers}`,
      icon: <CouriersIcon />,
      color: '#9c27b0',
    },
    {
      title: 'Total Revenue',
      value: formatCurrency(stats.total_revenue),
      icon: <RevenueIcon />,
      color: '#2e7d32',
    },
    {
      title: 'Avg Delivery Time',
      value: formatTime(stats.average_delivery_time),
      icon: <PerformanceIcon />,
      color: '#d32f2f',
    },
    {
      title: 'Success Rate',
      value: `${(stats.success_rate * 100).toFixed(1)}%`,
      icon: <PerformanceIcon />,
      color: '#2e7d32',
    },
  ];

  return (
    <Grid container spacing={3}>
      {statCards.map((card, index) => (
        <Grid item xs={12} sm={6} md={3} key={index}>
          <Card
            sx={{
              height: '100%',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 25px rgba(0,0,0,0.15)',
              },
            }}
          >
            <CardContent>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  mb: 2,
                }}
              >
                <Box>
                  <Typography
                    variant="h4"
                    sx={{
                      fontWeight: 700,
                      color: 'text.primary',
                      mb: 0.5,
                    }}
                  >
                    {card.value}
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ fontWeight: 500 }}
                  >
                    {card.title}
                  </Typography>
                </Box>
                <Avatar
                  sx={{
                    backgroundColor: card.color,
                    width: 56,
                    height: 56,
                  }}
                >
                  {card.icon}
                </Avatar>
              </Box>

              {card.change && (
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    mt: 1,
                  }}
                >
                  <Typography
                    variant="caption"
                    sx={{
                      color: card.changeColor || 'text.secondary',
                      fontWeight: 600,
                    }}
                  >
                    {card.change}
                  </Typography>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ ml: 1 }}
                  >
                    vs last week
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default StatsCards;
