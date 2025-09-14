import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  Chip,
  IconButton,
  Avatar,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  LocalShipping as ShippingIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';

import { ordersApi } from '../../../services/api';
import { OrderStatus } from '../../../types';
import LoadingSpinner from '../../../components/Common/LoadingSpinner';

const RecentOrders: React.FC = () => {
  const navigate = useNavigate();

  const { data: ordersData, isLoading } = useQuery(
    'recent-orders',
    () => ordersApi.getOrders({ page: 1, per_page: 5 }),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const getStatusColor = (status: OrderStatus) => {
    switch (status) {
      case OrderStatus.CREATED:
        return 'default';
      case OrderStatus.CONFIRMED:
        return 'info';
      case OrderStatus.ASSIGNED:
        return 'warning';
      case OrderStatus.PICKED_UP:
      case OrderStatus.IN_TRANSIT:
      case OrderStatus.OUT_FOR_DELIVERY:
        return 'primary';
      case OrderStatus.DELIVERED:
        return 'success';
      case OrderStatus.FAILED:
      case OrderStatus.CANCELLED:
        return 'error';
      default:
        return 'default';
    }
  };

  const formatStatus = (status: OrderStatus) => {
    return status.replace(/_/g, ' ').toUpperCase();
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));

    if (diffInMinutes < 60) {
      return `${diffInMinutes}m ago`;
    } else if (diffInMinutes < 1440) {
      return `${Math.floor(diffInMinutes / 60)}h ago`;
    } else {
      return `${Math.floor(diffInMinutes / 1440)}d ago`;
    }
  };

  const handleOrderClick = (orderId: string) => {
    navigate(`/orders/${orderId}`);
  };

  if (isLoading) {
    return (
      <Card sx={{ height: 400 }}>
        <CardContent sx={{ height: '100%' }}>
          <LoadingSpinner />
        </CardContent>
      </Card>
    );
  }

  const orders = ordersData?.data || [];

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
            Recent Orders
          </Typography>
          <Typography
            variant="caption"
            color="primary"
            sx={{
              cursor: 'pointer',
              '&:hover': { textDecoration: 'underline' },
            }}
            onClick={() => navigate('/orders')}
          >
            View All
          </Typography>
        </Box>

        {orders.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: 300,
            }}
          >
            <Typography color="text.secondary">
              No recent orders
            </Typography>
          </Box>
        ) : (
          <List sx={{ maxHeight: 320, overflow: 'auto' }}>
            {orders.map((order, index) => (
              <ListItem
                key={order.id}
                sx={{
                  px: 0,
                  py: 1.5,
                  borderBottom: index < orders.length - 1 ? '1px solid #f0f0f0' : 'none',
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: 'action.hover',
                    borderRadius: 1,
                  },
                }}
                onClick={() => handleOrderClick(order.id)}
              >
                <Avatar
                  sx={{
                    bgcolor: 'primary.main',
                    width: 40,
                    height: 40,
                    mr: 2,
                  }}
                >
                  <ShippingIcon />
                </Avatar>

                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        #{order.order_number}
                      </Typography>
                      <Chip
                        label={formatStatus(order.status)}
                        size="small"
                        color={getStatusColor(order.status) as any}
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    <Box sx={{ mt: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        {order.customer_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        {formatTime(order.created_at)}
                      </Typography>
                    </Box>
                  }
                />

                <Box sx={{ textAlign: 'right' }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    ${order.total_amount.toFixed(2)}
                  </Typography>
                  <IconButton size="small">
                    <MoreVertIcon fontSize="small" />
                  </IconButton>
                </Box>
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );
};

export default RecentOrders;
