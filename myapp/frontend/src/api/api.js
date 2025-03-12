import axios from 'axios';

// Base URL for API calls
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create an axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Water mains API endpoints
export const fetchWaterMains = async () => {
  try {
    const response = await api.get('/watermains/cached/');
    return response.data;
  } catch (error) {
    console.error('Error fetching water mains:', error);
    throw error;
  }
};

export const fetchWaterMainGeometries = async () => {
  try {
    const response = await api.get('/watermains/cached/geometry');
    return response.data;
  } catch (error) {
    console.error('Error fetching water main geometries:', error);
    throw error;
  }
};

export const fetchWaterMainById = async (id) => {
  try {
    const response = await api.get(`/watermains/cached/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching water main with ID ${id}:`, error);
    throw error;
  }
};

export default api; 