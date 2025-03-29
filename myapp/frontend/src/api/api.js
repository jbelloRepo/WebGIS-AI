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

// New chat API endpoint
export const sendChatQuery = async (message, sessionId = null) => {
  try {
    const response = await api.post('/chat/query', { message, session_id: sessionId });
    return response.data;
  } catch (error) {
    console.error('Error sending chat query:', error);
    throw error;
  }
};

// Create a new chat session
export const createChatSession = async () => {
  try {
    const response = await api.post('/chat/session');
    return response.data;
  } catch (error) {
    console.error('Error creating chat session:', error);
    throw error;
  }
};

// Get chat history for a session
export const getChatHistory = async (sessionId) => {
  try {
    const response = await api.get(`/chat/history/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching chat history:', error);
    throw error;
  }
};

// Add a new function to fetch geometry by specific IDs
export const fetchWaterMainGeometriesByIds = async (ids) => {
  try {
    console.log(`Attempting to filter ${ids.length} water mains`);
    
    // Convert array of IDs to comma-separated string
    const idsString = ids.join(',');
    console.log(`First few IDs: ${ids.slice(0, 5).join(',')}`);
    
    const response = await api.get(`/watermains/cached/geometry/${idsString}`);
    console.log(`Received ${response.data.length} geometries from server`);
    return response.data;
  } catch (error) {
    console.error('Error fetching water main geometries by IDs:', error);
    throw error;
  }
};

// Generate a filter token
export const createFilterToken = async (ids) => {
  try {
    console.log(`Creating filter token for ${ids.length} IDs`);
    const response = await api.post('/watermains/filter-token', { object_ids: ids });
    return response.data;
  } catch (error) {
    console.error('Error creating filter token:', error);
    throw error;
  }
};

// Fetch water mains using a token
export const fetchWaterMainsByToken = async (token) => {
  try {
    console.log(`Fetching water mains using token: ${token}`);
    const response = await api.get(`/watermains/cached/geometry/token/${token}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching water mains by token:', error);
    throw error;
  }
};

export const fetchDatasets = async () => {
  try {
    const response = await api.get('/datasets');
    return response.data;
  } catch (error) {
    console.error('Error fetching datasets:', error);
    throw error;
  }
};

export const validateArcGISEndpoint = async (url) => {
  try {
    const response = await fetch(url + '?f=json');
    if (!response.ok) {
      throw new Error('Invalid ArcGIS endpoint');
    }
    const data = await response.json();
    if (!data.type || !data.geometryType) {
      throw new Error('Invalid ArcGIS service endpoint');
    }
    return data;
  } catch (error) {
    console.error('Error validating ArcGIS endpoint:', error);
    throw error;
  }
};

export default api; 