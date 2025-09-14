// User types
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  workspace_id: string;
  created_at: string;
  updated_at: string;
}

export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  EMPLOYEE = 'employee',
  COURIER = 'courier',
}

export interface Workspace {
  id: string;
  name: string;
  description?: string;
  logo_url?: string;
  primary_color?: string;
  secondary_color?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Order types
export interface Order {
  id: string;
  order_number: string;
  customer_name: string;
  customer_email?: string;
  customer_phone?: string;
  pickup_address: string;
  delivery_address: string;
  package_description?: string;
  package_weight?: number;
  package_size: PackageSize;
  priority: OrderPriority;
  status: OrderStatus;
  scheduled_pickup?: string;
  scheduled_delivery?: string;
  actual_pickup?: string;
  actual_delivery?: string;
  delivery_fee: number;
  total_amount: number;
  notes?: string;
  tracking_code: string;
  courier_id?: string;
  workspace_id: string;
  created_at: string;
  updated_at: string;
}

export enum OrderStatus {
  CREATED = 'created',
  CONFIRMED = 'confirmed',
  ASSIGNED = 'assigned',
  PICKED_UP = 'picked_up',
  IN_TRANSIT = 'in_transit',
  OUT_FOR_DELIVERY = 'out_for_delivery',
  DELIVERED = 'delivered',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  RETURNED = 'returned',
}

export enum OrderPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent',
}

export enum PackageSize {
  SMALL = 'small',
  MEDIUM = 'medium',
  LARGE = 'large',
  EXTRA_LARGE = 'extra_large',
}

// Courier types
export interface Courier {
  id: string;
  user_id: string;
  user: User;
  status: CourierStatus;
  is_available: boolean;
  current_latitude?: number;
  current_longitude?: number;
  location_updated_at?: string;
  vehicle_type?: string;
  vehicle_plate?: string;
  vehicle_capacity?: number;
  max_delivery_distance?: number;
  working_hours_start?: string;
  working_hours_end?: string;
  working_days: number[];
  total_deliveries: number;
  successful_deliveries: number;
  average_rating?: number;
  current_route_id?: string;
  active_tasks_count: number;
  last_seen_at?: string;
  workspace_id: string;
  created_at: string;
  updated_at: string;
}

export enum CourierStatus {
  AVAILABLE = 'available',
  BUSY = 'busy',
  OFFLINE = 'offline',
  ON_BREAK = 'on_break',
}

// Route types
export interface Route {
  id: string;
  route_name: string;
  status: RouteStatus;
  courier_id?: string;
  courier?: Courier;
  total_distance_km?: number;
  estimated_duration_minutes?: number;
  total_orders: number;
  planned_start_time?: string;
  actual_start_time?: string;
  planned_end_time?: string;
  actual_end_time?: string;
  completed_tasks: number;
  failed_tasks: number;
  waypoints: any[];
  workspace_id: string;
  created_at: string;
  updated_at: string;
}

export enum RouteStatus {
  PENDING = 'pending',
  OPTIMIZING = 'optimizing',
  OPTIMIZED = 'optimized',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

// Task types
export interface Task {
  id: string;
  order_id: string;
  order?: Order;
  task_type: TaskType;
  courier_id?: string;
  courier?: Courier;
  route_id?: string;
  status: TaskStatus;
  sequence_number?: number;
  address: string;
  latitude?: number;
  longitude?: number;
  contact_name?: string;
  contact_phone?: string;
  scheduled_time?: string;
  estimated_arrival?: string;
  actual_arrival?: string;
  completed_at?: string;
  notes?: string;
  special_instructions?: string;
  completion_notes?: string;
  failure_reason?: string;
  customer_rating?: number;
  workspace_id: string;
  created_at: string;
  updated_at: string;
}

export enum TaskType {
  PICKUP = 'pickup',
  DELIVERY = 'delivery',
  RETURN = 'return',
}

export enum TaskStatus {
  PENDING = 'pending',
  ASSIGNED = 'assigned',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

// Analytics types
export interface DashboardStats {
  total_orders: number;
  active_orders: number;
  completed_orders: number;
  total_couriers: number;
  active_couriers: number;
  total_revenue: number;
  average_delivery_time: number;
  success_rate: number;
}

export interface ChartData {
  name: string;
  value: number;
  date?: string;
}

// API Response types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Form types
export interface LoginForm {
  email: string;
  password: string;
}

export interface RegisterForm {
  workspace_name: string;
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface OrderForm {
  customer_name: string;
  customer_email?: string;
  customer_phone?: string;
  pickup_address: string;
  delivery_address: string;
  package_description?: string;
  package_weight?: number;
  package_size: PackageSize;
  priority: OrderPriority;
  scheduled_pickup?: string;
  scheduled_delivery?: string;
  delivery_fee: number;
  notes?: string;
}

// Notification types
export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  read: boolean;
  created_at: string;
}
