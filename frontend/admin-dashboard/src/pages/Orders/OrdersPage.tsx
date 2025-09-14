import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Menu,
  MenuItem as MenuItemComponent,
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreVertIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';

import { ordersApi } from '../../services/api';
import { Order, OrderStatus, OrderPriority } from '../../types';
import LoadingSpinner from '../../components/Common/LoadingSpinner';

const OrdersPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const {
    data: ordersData,
    isLoading,
    error,
  } = useQuery(
    ['orders', page + 1, pageSize, searchTerm, statusFilter, priorityFilter],
    () => ordersApi.getOrders({
      page: page + 1,
      per_page: pageSize,
      search: searchTerm || undefined,
      status: statusFilter || undefined,
      priority: priorityFilter || undefined,
    }),
    {
      keepPreviousData: true,
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

  const getPriorityColor = (priority: OrderPriority) => {
    switch (priority) {
      case OrderPriority.LOW:
        return 'default';
      case OrderPriority.NORMAL:
        return 'info';
      case OrderPriority.HIGH:
        return 'warning';
      case OrderPriority.URGENT:
        return 'error';
      default:
        return 'default';
    }
  };

  const formatStatus = (status: OrderStatus) => {
    return status.replace(/_/g, ' ').toUpperCase();
  };

  const formatPriority = (priority: OrderPriority) => {
    return priority.toUpperCase();
  };

  const handleViewOrder = (id: string) => {
    navigate(`/orders/${id}`);
  };

  const handleEditOrder = (id: string) => {
    navigate(`/orders/${id}/edit`);
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const columns: GridColDef[] = [
    {
      field: 'order_number',
      headerName: 'Order #',
      width: 120,
      renderCell: (params) => (
        <Typography
          variant="body2"
          sx={{
            fontWeight: 600,
            color: 'primary.main',
            cursor: 'pointer',
          }}
          onClick={() => handleViewOrder(params.row.id)}
        >
          #{params.value}
        </Typography>
      ),
    },
    {
      field: 'customer_name',
      headerName: 'Customer',
      width: 180,
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 140,
      renderCell: (params) => (
        <Chip
          label={formatStatus(params.value)}
          size="small"
          color={getStatusColor(params.value) as any}
          variant="outlined"
        />
      ),
    },
    {
      field: 'priority',
      headerName: 'Priority',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={formatPriority(params.value)}
          size="small"
          color={getPriorityColor(params.value) as any}
          variant="filled"
        />
      ),
    },
    {
      field: 'pickup_address',
      headerName: 'Pickup',
      width: 200,
      renderCell: (params) => (
        <Typography variant="body2" noWrap>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'delivery_address',
      headerName: 'Delivery',
      width: 200,
      renderCell: (params) => (
        <Typography variant="body2" noWrap>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'total_amount',
      headerName: 'Amount',
      width: 100,
      renderCell: (params) => (
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          ${params.value.toFixed(2)}
        </Typography>
      ),
    },
    {
      field: 'created_at',
      headerName: 'Created',
      width: 120,
      renderCell: (params) => (
        <Typography variant="body2">
          {new Date(params.value).toLocaleDateString()}
        </Typography>
      ),
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 80,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<MoreVertIcon />}
          label="More"
          onClick={handleMenuClick}
        />,
      ],
    },
  ];

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography color="error">
          Failed to load orders. Please try again.
        </Typography>
      </Box>
    );
  }

  const orders = ordersData?.data || [];
  const totalCount = ordersData?.total || 0;

  return (
    <Routes>
      <Route
        index
        element={
          <Box>
            {/* Page Header */}
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                mb: 4,
              }}
            >
              <Box>
                <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
                  Orders
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Manage and track all delivery orders
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={handleMenuClick}
                >
                  Export
                </Button>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => navigate('/orders/new')}
                >
                  New Order
                </Button>
              </Box>
            </Box>

            {/* Filters */}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    gap: 2,
                    flexWrap: 'wrap',
                    alignItems: 'center',
                  }}
                >
                  <TextField
                    placeholder="Search orders..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    size="small"
                    sx={{ minWidth: 250 }}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <SearchIcon />
                        </InputAdornment>
                      ),
                    }}
                  />

                  <FormControl size="small" sx={{ minWidth: 150 }}>
                    <InputLabel>Status</InputLabel>
                    <Select
                      value={statusFilter}
                      label="Status"
                      onChange={(e) => setStatusFilter(e.target.value)}
                    >
                      <MenuItem value="">All Statuses</MenuItem>
                      {Object.values(OrderStatus).map((status) => (
                        <MenuItem key={status} value={status}>
                          {formatStatus(status)}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl size="small" sx={{ minWidth: 150 }}>
                    <InputLabel>Priority</InputLabel>
                    <Select
                      value={priorityFilter}
                      label="Priority"
                      onChange={(e) => setPriorityFilter(e.target.value)}
                    >
                      <MenuItem value="">All Priorities</MenuItem>
                      {Object.values(OrderPriority).map((priority) => (
                        <MenuItem key={priority} value={priority}>
                          {formatPriority(priority)}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <IconButton>
                    <FilterIcon />
                  </IconButton>
                </Box>
              </CardContent>
            </Card>

            {/* Data Grid */}
            <Card>
              <DataGrid
                rows={orders}
                columns={columns}
                paginationMode="server"
                rowCount={totalCount}
                paginationModel={{ page, pageSize }}
                onPaginationModelChange={(model) => {
                  setPage(model.page);
                  setPageSize(model.pageSize);
                }}
                pageSizeOptions={[10, 25, 50, 100]}
                loading={isLoading}
                disableRowSelectionOnClick
                autoHeight
                sx={{
                  border: 'none',
                  '& .MuiDataGrid-cell': {
                    borderBottom: '1px solid #f0f0f0',
                  },
                  '& .MuiDataGrid-columnHeaders': {
                    backgroundColor: '#fafafa',
                    borderBottom: '2px solid #e0e0e0',
                  },
                }}
              />
            </Card>

            {/* Context Menu */}
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
            >
              <MenuItemComponent onClick={handleMenuClose}>
                Export CSV
              </MenuItemComponent>
              <MenuItemComponent onClick={handleMenuClose}>
                Export PDF
              </MenuItemComponent>
            </Menu>
          </Box>
        }
      />
      <Route path="new" element={<div>Create New Order</div>} />
      <Route path=":id" element={<div>Order Details</div>} />
      <Route path=":id/edit" element={<div>Edit Order</div>} />
    </Routes>
  );
};

export default OrdersPage;
