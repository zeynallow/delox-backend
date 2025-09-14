import React, { useEffect, useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Fullscreen as FullscreenIcon,
} from '@mui/icons-material';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Icon } from 'leaflet';
import { useQuery } from 'react-query';

import { couriersApi } from '../../../services/api';
import { CourierStatus } from '../../../types';
import LoadingSpinner from '../../../components/Common/LoadingSpinner';

// Fix for default markers in react-leaflet
delete (Icon.Default.prototype as any)._getIconUrl;
Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const CourierMap: React.FC = () => {
  const [mapKey, setMapKey] = useState(0);

  const {
    data: couriers,
    isLoading,
    refetch,
  } = useQuery(
    'courier-locations',
    couriersApi.getLiveLocations,
    {
      refetchInterval: 10000, // Refresh every 10 seconds
    }
  );

  const handleRefresh = () => {
    refetch();
  };

  const handleFullscreen = () => {
    // Implement fullscreen functionality
    setMapKey(prev => prev + 1);
  };

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

  const createCustomIcon = (status: CourierStatus) => {
    const color = status === CourierStatus.AVAILABLE ? 'green' : 
                  status === CourierStatus.BUSY ? 'orange' :
                  status === CourierStatus.ON_BREAK ? 'blue' : 'red';
    
    return new Icon({
      iconUrl: `data:image/svg+xml;base64,${btoa(`
        <svg width="25" height="41" viewBox="0 0 25 41" xmlns="http://www.w3.org/2000/svg">
          <path d="M12.5 0C5.6 0 0 5.6 0 12.5C0 19.4 12.5 41 12.5 41S25 19.4 25 12.5C25 5.6 19.4 0 12.5 0Z" fill="${color}"/>
          <circle cx="12.5" cy="12.5" r="6" fill="white"/>
        </svg>
      `)}`,
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
    });
  };

  // Default center (you can adjust this based on your location)
  const defaultCenter: [number, number] = [40.7128, -74.0060]; // New York City

  if (isLoading) {
    return (
      <Card sx={{ height: 500 }}>
        <CardContent sx={{ height: '100%' }}>
          <LoadingSpinner />
        </CardContent>
      </Card>
    );
  }

  const activeCouriers = couriers?.filter(courier => 
    courier.current_latitude && 
    courier.current_longitude &&
    courier.status !== CourierStatus.OFFLINE
  ) || [];

  return (
    <Card sx={{ height: 500 }}>
      <CardContent sx={{ height: '100%', p: 0 }}>
        {/* Header */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            p: 2,
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Live Courier Tracking
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {activeCouriers.length} active couriers
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Refresh">
              <IconButton onClick={handleRefresh} size="small">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Fullscreen">
              <IconButton onClick={handleFullscreen} size="small">
                <FullscreenIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Legend */}
        <Box
          sx={{
            display: 'flex',
            gap: 1,
            p: 2,
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <Chip
            label="Available"
            size="small"
            color="success"
            variant="outlined"
          />
          <Chip
            label="Busy"
            size="small"
            color="warning"
            variant="outlined"
          />
          <Chip
            label="On Break"
            size="small"
            color="info"
            variant="outlined"
          />
          <Chip
            label="Offline"
            size="small"
            color="error"
            variant="outlined"
          />
        </Box>

        {/* Map */}
        <Box sx={{ height: 'calc(100% - 120px)' }}>
          {activeCouriers.length === 0 ? (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
              }}
            >
              <Typography color="text.secondary">
                No active couriers with location data
              </Typography>
            </Box>
          ) : (
            <MapContainer
              key={mapKey}
              center={
                activeCouriers.length > 0 && activeCouriers[0].current_latitude
                  ? [activeCouriers[0].current_latitude, activeCouriers[0].current_longitude!]
                  : defaultCenter
              }
              zoom={13}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              
              {activeCouriers.map((courier) => (
                <Marker
                  key={courier.id}
                  position={[courier.current_latitude!, courier.current_longitude!]}
                  icon={createCustomIcon(courier.status)}
                >
                  <Popup>
                    <Box sx={{ minWidth: 200 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                        {courier.user.first_name} {courier.user.last_name}
                      </Typography>
                      
                      <Box sx={{ mb: 1 }}>
                        <Chip
                          label={courier.status.toUpperCase()}
                          size="small"
                          color={getStatusColor(courier.status) as any}
                          variant="outlined"
                        />
                      </Box>

                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Active Tasks: {courier.active_tasks_count}
                      </Typography>
                      
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Total Deliveries: {courier.total_deliveries}
                      </Typography>

                      {courier.vehicle_type && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                          Vehicle: {courier.vehicle_type}
                        </Typography>
                      )}

                      {courier.location_updated_at && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                          Last updated: {new Date(courier.location_updated_at).toLocaleTimeString()}
                        </Typography>
                      )}
                    </Box>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default CourierMap;
