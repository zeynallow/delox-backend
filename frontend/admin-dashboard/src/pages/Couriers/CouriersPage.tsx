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
  Avatar,
  IconButton,
  Menu,
  MenuItem as MenuItemComponent,
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreVertIcon,
  LocationOn as LocationIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';

import { couriersApi } from '../../services/api';
import { Courier, CourierStatus } from '../../types';
import LoadingSpinner from '../../components/Common/LoadingSpinner';

const CouriersPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const {
    data: couriersData,
    isLoading,
    error,
  } = useQuery(
    ['couriers', page + 1, pageSize, searchTerm, statusFilter],
    () => couriersApi.getCouriers({
      page: page + 1,
      per_page: pageSize,
      status: statusFilter || undefined,
    }),
    {
      keepPreviousData: true,
    }
  );

  const getStatusColor = (status: CourierStatus) => {
    switch (status) {
      case CourierStatus.AVAILABLE:
        return 'success';
      case CourierStatus.BUSY:
        return 'warning';
      case CourierStatus.ON_BREAK:
        return 'info';
      case CourierStatus.OFFLINE:
        return 'error';
      default:
        return 'default';
    }
  };

  const formatStatus = (status: CourierStatus) => {
    return status.replace(/_/g, ' ').toUpperCase();
  };

  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName[0]}${lastName[0]}`.toUpperCase();
  };

  const handleViewCourier = (id: string) => {
    navigate(`/couriers/${id}`);
  };

  const handleEditCourier = (id: string) => {
    navigate(`/couriers/${id}/edit`);
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const columns: GridColDef[] = [
    {
      field: 'user',
      headerName: 'Courier',
      width: 200,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
            {getInitials(params.value.first_name, params.value.last_name)}
          </Avatar>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {params.value.first_name} {params.value.last_name}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {params.value.email}
            </Typography>
          </Box>
        </Box>
      ),
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
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
      field: 'is_available',
      headerName: 'Available',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Yes' : 'No'}
          size="small"
          color={params.value ? 'success' : 'default'}
          variant="outlined"
        />
      ),
    },
    {
      field: 'vehicle_type',
      headerName: 'Vehicle',
      width: 120,
      renderCell: (params) => (
        <Typography variant="body2">
          {params.value || 'Not specified'}
        </Typography>
      ),
    },
    {
      field: 'active_tasks_count',
      headerName: 'Active Tasks',
      width: 120,
      renderCell: (params) => (
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'total_deliveries',
      headerName: 'Total Deliveries',
      width: 140,
      renderCell: (params) => (
        <Typography variant="body2">
          {params.value.toLocaleString()}
        </Typography>
      ),
    },
    {
      field: 'successful_deliveries',
      headerName: 'Success Rate',
      width: 120,
      renderCell: (params) => {
        const rate = params.row.total_deliveries > 0 
          ? (params.value / params.row.total_deliveries * 100).toFixed(1)
          : '0';
        return (
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {rate}%
          </Typography>
        );
      },
    },
    {
      field: 'average_rating',
      headerName: 'Rating',
      width: 100,
      renderCell: (params) => (
        <Typography variant="body2">
          {params.value ? `⭐ ${params.value.toFixed(1)}` : 'N/A'}
        </Typography>
      ),
    },
    {
      field: 'location',
      headerName: 'Location',
      width: 100,
      renderCell: (params) => (
        <IconButton
          size="small"
          disabled={!params.row.current_latitude || !params.row.current_longitude}
          onClick={() => {
            // Open location in map
            if (params.row.current_latitude && params.row.current_longitude) {
              window.open(
                `https://maps.google.com/?q=${params.row.current_latitude},${params.row.current_longitude}`,
                '_blank'
              );
            }
          }}
        >
          <LocationIcon 
            color={params.row.current_latitude ? 'primary' : 'disabled'} 
          />
        </IconButton>
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
          Failed to load couriers. Please try again.
        </Typography>
      </Box>
    );
  }

  const couriers = couriersData?.data || [];
  const totalCount = couriersData?.total || 0;

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
                  Couriers
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Manage courier accounts and track performance
                </Typography>
              </Box>

              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => navigate('/couriers/new')}
              >
                Add Courier
              </Button>
            </Box>

            {/* Stats Cards */}
            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <Card sx={{ flex: 1 }}>
                <CardContent>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main' }}>
                    {couriers.filter(c => c.status === CourierStatus.AVAILABLE).length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Available
                  </Typography>
                </CardContent>
              </Card>
              <Card sx={{ flex: 1 }}>
                <CardContent>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'warning.main' }}>
                    {couriers.filter(c => c.status === CourierStatus.BUSY).length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Busy
                  </Typography>
                </CardContent>
              </Card>
              <Card sx={{ flex: 1 }}>
                <CardContent>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'error.main' }}>
                    {couriers.filter(c => c.status === CourierStatus.OFFLINE).length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Offline
                  </Typography>
                </CardContent>
              </Card>
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
                    placeholder="Search couriers..."
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
                      {Object.values(CourierStatus).map((status) => (
                        <MenuItem key={status} value={status}>
                          {formatStatus(status)}
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
                rows={couriers}
                columns={columns}
                paginationMode="server"
                rowCount={totalCount}
                page={page}
                pageSize={pageSize}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
                rowsPerPageOptions={[10, 25, 50, 100]}
                loading={isLoading}
                disableSelectionOnClick
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
                View Details
              </MenuItemComponent>
              <MenuItemComponent onClick={handleMenuClose}>
                Edit Courier
              </MenuItemComponent>
              <MenuItemComponent onClick={handleMenuClose}>
                View Location
              </MenuItemComponent>
              <MenuItemComponent onClick={handleMenuClose}>
                Assign Task
              </MenuItemComponent>
            </Menu>
          </Box>
        }
      />
      <Route path="new" element={<div>Add New Courier</div>} />
      <Route path=":id" element={<div>Courier Details</div>} />
      <Route path=":id/edit" element={<div>Edit Courier</div>} />
    </Routes>
  );
};

export default CouriersPage;
