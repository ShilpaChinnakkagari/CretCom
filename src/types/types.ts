export interface User {
  id: string;
  name: string;
  password: string;
  role: string;
  email?: string;
}

export interface Department {
  id: number;
  name: string;
  hod: string;
  faculty: number;
  students: number;
  status: string;
}

export interface Stats {
  totalStudents: number;
  placementRate: number;
  totalFaculty: number;
  feeCollection: string;
  departments: number;
  avgAttendance: number;
}