import React, { useState, useRef, useEffect } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import { useSnackbar } from 'notistack';
import { validateArcGISEndpoint } from '../api/api';
import api from '../api/api';

function AddDatasetDialog({ open, onClose, onSuccess }) {
  const [url, setUrl] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const { enqueueSnackbar } = useSnackbar();
  const statusCheckInterval = useRef(null);

  useEffect(() => {
    return () => {
      if (statusCheckInterval.current) {
        clearInterval(statusCheckInterval.current);
      }
    };
  }, []);

  // Reset error when url changes
  useEffect(() => {
    setError(null);
  }, [url]);

  // Add this to check if sessionId is actually available
  useEffect(() => {
    const currentSessionId = localStorage.getItem('chatSessionId');
    console.log("Current session ID from localStorage:", currentSessionId);
    // If no session ID, we could potentially create one here
  }, []);

  const checkStatus = async (tableName) => {
    try {
      const response = await api.get(`/datasets/${tableName}/status`);
      const data = response.data;
      setStatus(data.status);
      setProgress(data.progress);

      switch (data.status) {
        case 'validating':
          enqueueSnackbar('Validating ArcGIS endpoint...', { variant: 'info' });
          break;
        case 'schema_generation':
          enqueueSnackbar('Generating database schema...', { variant: 'info' });
          break;
        case 'creating_table':
          enqueueSnackbar('Creating database table...', { variant: 'info' });
          break;
        case 'loading':
          // Progress is shown in the dialog
          break;
        case 'complete':
          clearInterval(statusCheckInterval.current);
          setLoading(false);
          enqueueSnackbar('Dataset loaded successfully!', { variant: 'success' });
          // This is where we notify the parent that the dataset is done
          onSuccess(); 
          onClose();
          break;
        case 'error':
          clearInterval(statusCheckInterval.current);
          setLoading(false);
          setError(data.message || 'Failed to load dataset');
          enqueueSnackbar(data.message || 'Failed to load dataset', { variant: 'error' });
          break;
        default:
          break;
      }
    } catch (error) {
      console.error('Error checking status:', error);
      setError('Failed to check dataset status');
    }
  };

  // Function to check if URL is valid
  const isValidUrl = (url) => {
    try {
      new URL(url);
      // Check if it's ArcGIS-like
      return url.includes('arcgis.com') || 
             url.includes('FeatureServer') || 
             url.includes('MapServer');
    } catch (e) {
      return false;
    }
  };

  const validateAndSubmit = async (e) => {
    e.preventDefault();
    
    // Get the latest sessionId value right before sending
    const currentSessionId = localStorage.getItem('chatSessionId');
    console.log("Session ID at submission time:", currentSessionId);
    
    if (!isValidUrl(url)) {
      setError('Please enter a valid ArcGIS REST service URL');
      return;
    }
    
    setLoading(true);
    setProgress(0);
    setError(null);
    
    try {
      // Validate the ArcGIS endpoint
      enqueueSnackbar('Validating ArcGIS endpoint...', { variant: 'info' });
      await validateArcGISEndpoint(url);
      
      // Register the dataset with the latest session ID
      const response = await api.post('/datasets/register', { 
        base_url: url,
        name,
        table_name: name.toLowerCase().replace(/\s+/g, '_'),
        session_id: currentSessionId  // Use the latest value
      });

      const data = response.data;
      setStatus('initializing');
      enqueueSnackbar('Dataset registration started...', { variant: 'info' });
      
      // Poll for status every 2s
      statusCheckInterval.current = setInterval(
        () => checkStatus(data.table_name),
        2000
      );
      
    } catch (error) {
      console.error('Error registering dataset:', error);
      setLoading(false);
      setError(error.message);
      enqueueSnackbar(error.message, { variant: 'error' });
    }
  };

  const getStatusMessage = () => {
    switch (status) {
      case 'initializing':
        return 'Initializing dataset...';
      case 'validating':
        return 'Validating ArcGIS endpoint...';
      case 'schema_generation':
        return 'Generating database schema...';
      case 'creating_table':
        return 'Creating database table...';
      case 'loading':
        return `Loading data (${progress}% complete)...`;
      case 'complete':
        return 'Dataset loaded successfully!';
      case 'error':
        return 'Error loading dataset';
      default:
        return '';
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={loading ? undefined : onClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>Add Dataset from ArcGIS REST Endpoint</DialogTitle>
      <form onSubmit={validateAndSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <TextField
            autoFocus
            margin="dense"
            label="Dataset Name"
            fullWidth
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={loading}
            required
            helperText="Enter a unique name for this dataset"
          />
          <TextField
            margin="dense"
            label="ArcGIS REST Endpoint URL"
            fullWidth
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
            required
            helperText="Example: https://services.arcgis.com/.../FeatureServer/0"
          />
          {loading && (
            <Box sx={{ width: '100%', mt: 2 }}>
              <LinearProgress 
                variant={progress > 0 ? "determinate" : "indeterminate"} 
                value={progress} 
              />
              <Typography 
                variant="body2" 
                color="text.secondary" 
                align="center" 
                sx={{ mt: 1 }}
              >
                {getStatusMessage()}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button 
            type="submit" 
            variant="contained"
            disabled={loading || !url || !name}
          >
            {loading ? 'Processing...' : 'Add Dataset'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

export default AddDatasetDialog;
