import { useState, useEffect } from 'react';
import { apiService } from '../services/api';

function HealthCheck() {
  const [status, setStatus] = useState({
    loading: true,
    data: null,
    error: null,
  });

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    setStatus({ loading: true, data: null, error: null });
    try {
      const response = await apiService.healthCheck();
      setStatus({ loading: false, data: response.data, error: null });
    } catch (error) {
      setStatus({
        loading: false,
        data: null,
        error: error.message || 'Failed to connect to backend',
      });
    }
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Backend Connection Status</h2>

      {status.loading && (
        <div style={styles.loading}>Checking connection...</div>
      )}

      {status.error && (
        <div style={styles.error}>
          <p style={styles.errorText}>❌ Error: {status.error}</p>
          <p style={styles.errorHint}>
            Make sure the Django backend is running at http://localhost:8000
          </p>
        </div>
      )}

      {status.data && (
        <div style={styles.success}>
          <p style={styles.successText}>✅ {status.data.message}</p>
          <p style={styles.statusText}>Status: {status.data.status}</p>
        </div>
      )}

      <button onClick={checkHealth} style={styles.button}>
        Check Again
      </button>
    </div>
  );
}

const styles = {
  container: {
    padding: '20px',
    maxWidth: '600px',
    margin: '0 auto',
    textAlign: 'center',
  },
  title: {
    color: '#333',
    marginBottom: '20px',
  },
  loading: {
    padding: '20px',
    color: '#666',
    fontSize: '16px',
  },
  error: {
    backgroundColor: '#fee',
    border: '1px solid #fcc',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '20px',
  },
  errorText: {
    color: '#c33',
    margin: '0 0 10px 0',
    fontSize: '16px',
  },
  errorHint: {
    color: '#666',
    fontSize: '14px',
    margin: 0,
  },
  success: {
    backgroundColor: '#efe',
    border: '1px solid #cfc',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '20px',
  },
  successText: {
    color: '#393',
    margin: '0 0 10px 0',
    fontSize: '18px',
    fontWeight: 'bold',
  },
  statusText: {
    color: '#666',
    margin: 0,
    fontSize: '14px',
  },
  button: {
    backgroundColor: '#4CAF50',
    color: 'white',
    padding: '12px 24px',
    fontSize: '16px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'background-color 0.3s',
  },
};

export default HealthCheck;
