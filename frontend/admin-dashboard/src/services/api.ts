import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  User, 
  Order, 
  Courier, 
  Route, 
  Task, 
  LoginForm, 
  RegisterForm, 
  OrderForm,
  ApiResponse,
  PaginatedResponse,
  DashboardStats
} from '../types';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await authApi.refreshToken(refreshToken);
          localStorage.setItem('access_token', response.access_token);
          
          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${response.access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: async (credentials: LoginForm): Promise<{ access_token: string; refresh_token: string }> => {
    const response: AxiosResponse<{ access_token: string; refresh_token: string }> = 
      await api.post('/auth/login', credentials);
    return response.data;
  },

  register: async (data: RegisterForm): Promise<{ access_token: string; refresh_token: string }> => {
    const response: AxiosResponse<{ access_token: string; refresh_token: string }> = 
      await api.post('/auth/register', data);
    return response.data;
  },

  refreshToken: async (refresh_token: string): Promise<{ access_token: string }> => {
    const response: AxiosResponse<{ access_token: string }> = 
      await api.post('/auth/refresh', { refresh_token });
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response: AxiosResponse<ApiResponse<User>> = await api.get('/users/me');
    return response.data.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },
};

// Users API
export const usersApi = {
  getUsers: async (params?: { page?: number; per_page?: number; role?: string }): Promise<PaginatedResponse<User>> => {
    const response: AxiosResponse<PaginatedResponse<User>> = await api.get('/users', { params });
    return response.data;
  },

  getUser: async (id: string): Promise<User> => {
    const response: AxiosResponse<ApiResponse<User>> = await api.get(`/users/${id}`);
    return response.data.data;
  },

  createUser: async (data: Partial<User>): Promise<User> => {
    const response: AxiosResponse<ApiResponse<User>> = await api.post('/users', data);
    return response.data.data;
  },

  updateUser: async (id: string, data: Partial<User>): Promise<User> => {
    const response: AxiosResponse<ApiResponse<User>> = await api.put(`/users/${id}`, data);
    return response.data.data;
  },

  deleteUser: async (id: string): Promise<void> => {
    await api.delete(`/users/${id}`);
  },
};

// Orders API
export const ordersApi = {
  getOrders: async (params?: { 
    page?: number; 
    per_page?: number; 
    status?: string;
    priority?: string;
    search?: string;
  }): Promise<PaginatedResponse<Order>> => {
    const response: AxiosResponse<PaginatedResponse<Order>> = await api.get('/orders', { params });
    return response.data;
  },

  getOrder: async (id: string): Promise<Order> => {
    const response: AxiosResponse<ApiResponse<Order>> = await api.get(`/orders/${id}`);
    return response.data.data;
  },

  createOrder: async (data: OrderForm): Promise<Order> => {
    const response: AxiosResponse<ApiResponse<Order>> = await api.post('/orders', data);
    return response.data.data;
  },

  updateOrder: async (id: string, data: Partial<OrderForm>): Promise<Order> => {
    const response: AxiosResponse<ApiResponse<Order>> = await api.put(`/orders/${id}`, data);
    return response.data.data;
  },

  deleteOrder: async (id: string): Promise<void> => {
    await api.delete(`/orders/${id}`);
  },

  assignCourier: async (orderId: string, courierId: string): Promise<Order> => {
    const response: AxiosResponse<ApiResponse<Order>> = 
      await api.put(`/orders/${orderId}/assign`, { courier_id: courierId });
    return response.data.data;
  },

  updateStatus: async (orderId: string, status: string): Promise<Order> => {
    const response: AxiosResponse<ApiResponse<Order>> = 
      await api.put(`/orders/${orderId}/status`, { status });
    return response.data.data;
  },
};

// Couriers API
export const couriersApi = {
  getCouriers: async (params?: { 
    page?: number; 
    per_page?: number; 
    status?: string;
    available_only?: boolean;
  }): Promise<PaginatedResponse<Courier>> => {
    const response: AxiosResponse<PaginatedResponse<Courier>> = await api.get('/couriers', { params });
    return response.data;
  },

  getCourier: async (id: string): Promise<Courier> => {
    const response: AxiosResponse<ApiResponse<Courier>> = await api.get(`/couriers/${id}`);
    return response.data.data;
  },

  createCourier: async (data: Partial<Courier>): Promise<Courier> => {
    const response: AxiosResponse<ApiResponse<Courier>> = await api.post('/couriers', data);
    return response.data.data;
  },

  updateCourier: async (id: string, data: Partial<Courier>): Promise<Courier> => {
    const response: AxiosResponse<ApiResponse<Courier>> = await api.put(`/couriers/${id}`, data);
    return response.data.data;
  },

  deleteCourier: async (id: string): Promise<void> => {
    await api.delete(`/couriers/${id}`);
  },

  getLiveLocations: async (): Promise<Courier[]> => {
    const response: AxiosResponse<ApiResponse<Courier[]>> = await api.get('/tracking/couriers/live');
    return response.data.data;
  },
};

// Routes API
export const routesApi = {
  getRoutes: async (params?: { 
    page?: number; 
    per_page?: number; 
    status?: string;
    courier_id?: string;
  }): Promise<PaginatedResponse<Route>> => {
    const response: AxiosResponse<PaginatedResponse<Route>> = await api.get('/routes', { params });
    return response.data;
  },

  getRoute: async (id: string): Promise<Route> => {
    const response: AxiosResponse<ApiResponse<Route>> = await api.get(`/routes/${id}`);
    return response.data.data;
  },

  createRoute: async (data: Partial<Route>): Promise<Route> => {
    const response: AxiosResponse<ApiResponse<Route>> = await api.post('/routes', data);
    return response.data.data;
  },

  optimizeRoutes: async (data: { courier_ids: string[]; order_ids: string[] }): Promise<any> => {
    const response: AxiosResponse<ApiResponse<any>> = await api.post('/routes/optimize', data);
    return response.data.data;
  },
};

// Tasks API
export const tasksApi = {
  getTasks: async (params?: { 
    page?: number; 
    per_page?: number; 
    status?: string;
    courier_id?: string;
  }): Promise<PaginatedResponse<Task>> => {
    const response: AxiosResponse<PaginatedResponse<Task>> = await api.get('/tasks', { params });
    return response.data;
  },

  getTask: async (id: string): Promise<Task> => {
    const response: AxiosResponse<ApiResponse<Task>> = await api.get(`/tasks/${id}`);
    return response.data.data;
  },

  updateTask: async (id: string, data: Partial<Task>): Promise<Task> => {
    const response: AxiosResponse<ApiResponse<Task>> = await api.put(`/tasks/${id}`, data);
    return response.data.data;
  },
};

// Analytics API
export const analyticsApi = {
  getDashboardStats: async (): Promise<DashboardStats> => {
    const response: AxiosResponse<ApiResponse<DashboardStats>> = await api.get('/analytics/dashboard');
    return response.data.data;
  },

  getOrdersChart: async (days: number = 7): Promise<any[]> => {
    const response: AxiosResponse<ApiResponse<any[]>> = 
      await api.get(`/analytics/orders-chart?days=${days}`);
    return response.data.data;
  },

  getRevenueChart: async (days: number = 30): Promise<any[]> => {
    const response: AxiosResponse<ApiResponse<any[]>> = 
      await api.get(`/analytics/revenue-chart?days=${days}`);
    return response.data.data;
  },

  getCourierPerformance: async (days: number = 7): Promise<any[]> => {
    const response: AxiosResponse<ApiResponse<any[]>> = 
      await api.get(`/analytics/courier-performance?days=${days}`);
    return response.data.data;
  },
};

export default api;
