import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api', // The FastAPI backend is served on the same origin
});

// We will need a way to set the token for authenticated requests
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('jwt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const login = async (username, password) => {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);

  // FastAPI's OAuth2PasswordBearer expects a form-encoded payload
  const response = await apiClient.post('/token', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

// We will add more functions here for other API calls
// e.g., getRooms, createRoom, etc.

export default apiClient;
