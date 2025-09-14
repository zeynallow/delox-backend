import React from 'react';
import { Grid, Typography, Box } from '@mui/material';
import { useQuery } from 'react-query';

import { analyticsApi } from '../../services/api';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import StatsCards from './components/StatsCards';
import OrdersChart from './components/OrdersChart';
import RevenueChart from './components/RevenueChart';
import CourierMap from './components/CourierMap';
import RecentOrders from './components/RecentOrders';
import CourierPerformance from './components/CourierPerformance';

const DashboardPage: React.FC = () => {
  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery('dashboard-stats', analyticsApi.getDashboardStats, {
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const {
    data: ordersChart,
    isLoading: ordersChartLoading,
  } = useQuery('orders-chart', () => analyticsApi.getOrdersChart(7), {
    refetchInterval: 60000, // Refresh every minute
  });

  const {
    data: revenueChart,
    isLoading: revenueChartLoading,
  } = useQuery('revenue-chart', () => analyticsApi.getRevenueChart(30), {
    refetchInterval: 60000,
  });

  const {
    data: courierPerformance,
    isLoading: courierPerformanceLoading,
  } = useQuery('courier-performance', () => analyticsApi.getCourierPerformance(7), {
    refetchInterval: 60000,
  });

  if (statsLoading) {
    return <LoadingSpinner />;
  }

  if (statsError) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography color="error">
          Failed to load dashboard data. Please try again.
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
          Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome back! Here's what's happening with your deliveries today.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Stats Cards */}
        <Grid item xs={12}>
          <StatsCards stats={stats} />
        </Grid>

        {/* Charts Row */}
        <Grid item xs={12} md={8}>
          <Grid container spacing={3}>
            {/* Orders Chart */}
            <Grid item xs={12}>
              <OrdersChart 
                data={ordersChart} 
                loading={ordersChartLoading} 
              />
            </Grid>

            {/* Revenue Chart */}
            <Grid item xs={12}>
              <RevenueChart 
                data={revenueChart} 
                loading={revenueChartLoading} 
              />
            </Grid>
          </Grid>
        </Grid>

        {/* Right Sidebar */}
        <Grid item xs={12} md={4}>
          <Grid container spacing={3}>
            {/* Courier Performance */}
            <Grid item xs={12}>
              <CourierPerformance 
                data={courierPerformance} 
                loading={courierPerformanceLoading} 
              />
            </Grid>

            {/* Recent Orders */}
            <Grid item xs={12}>
              <RecentOrders />
            </Grid>
          </Grid>
        </Grid>

        {/* Courier Map */}
        <Grid item xs={12}>
          <CourierMap />
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage;
